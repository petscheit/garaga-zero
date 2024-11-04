from random import randint

from garaga.definitions import CURVES, STARK, CurveID, G1Point, G2Point, ISOGENY_MAP_G2
from garaga.extension_field_modulo_circuit import ExtensionFieldModuloCircuit
import garaga.modulo_circuit_structs as structs

from garaga.modulo_circuit import WriteOps
from garaga.precompiled_circuits import (
    final_exp,
    multi_miller_loop,
    multi_pairing_check,
)
from garaga.precompiled_circuits.compilable_circuits.base import (
    BaseEXTFCircuit,
    BaseModuloCircuit,
    ModuloCircuit,
    ModuloCircuitElement,
    PyFelt,
)
from garaga.precompiled_circuits.map_to_curve import MapToCurveG2
from garaga.precompiled_circuits.isogeny import IsogenyG2
from garaga.precompiled_circuits.ec import DerivePointFromX
from garaga.algebra import Fp2


class DerivePointFromXCircuit(BaseModuloCircuit):
    def __init__(
        self, curve_id: int, auto_run: bool = True, compilation_mode: int = 0
    ) -> None:
        super().__init__(
            name="derive_point_from_x",
            curve_id=curve_id,
            auto_run=auto_run,
            compilation_mode=compilation_mode,
        )

    def build_input(self) -> list[PyFelt]:
        input = []
        input.append(self.field(randint(0, STARK - 1)))
        input.append(self.field(CURVES[self.curve_id].a))
        input.append(self.field(CURVES[self.curve_id].b))  # y^2 = x^3 + b
        input.append(self.field(CURVES[self.curve_id].fp_generator))
        return input

    def _run_circuit_inner(self, input: list[PyFelt]) -> ModuloCircuit:
        circuit = DerivePointFromX(
            self.name, self.curve_id, compilation_mode=self.compilation_mode
        )
        x, a, b, g = circuit.write_elements(input[0:4], WriteOps.INPUT)
        rhs, grhs, should_be_rhs, should_be_grhs, y_try = circuit._derive_point_from_x(
            x, a, b, g
        )
        circuit.extend_output([rhs, grhs, should_be_rhs, should_be_grhs, y_try])

        return circuit


class FP12MulCircuit(BaseEXTFCircuit):
    def __init__(
        self,
        curve_id: int,
        auto_run: bool = True,
        init_hash: int = None,
        compilation_mode: int = 0,
    ):
        super().__init__(
            "fp12_mul", 24, curve_id, auto_run, init_hash, compilation_mode
        )

    def build_input(self) -> list[PyFelt]:
        return [self.field(randint(0, self.field.p - 1)) for _ in range(self.input_len)]

    def _run_circuit_inner(self, input: list[PyFelt]) -> ExtensionFieldModuloCircuit:
        circuit = ExtensionFieldModuloCircuit(
            self.name,
            self.curve_id,
            extension_degree=12,
            init_hash=self.init_hash,
            compilation_mode=self.compilation_mode,
        )
        X = circuit.write_elements(input[0:12], WriteOps.INPUT)
        Y = circuit.write_elements(input[12:24], WriteOps.INPUT)
        xy = circuit.extf_mul([X, Y], 12)
        circuit.extend_output(xy)
        circuit.finalize_circuit()

        return circuit


class FinalExpPart1Circuit(BaseEXTFCircuit):
    def __init__(
        self,
        curve_id: int,
        auto_run: bool = True,
        init_hash: int = None,
        compilation_mode: int = 0,
    ):
        super().__init__(
            "final_exp_part_1", 12, curve_id, auto_run, init_hash, compilation_mode
        )

    def build_input(self) -> list[PyFelt]:
        return [self.field(randint(0, self.field.p - 1)) for _ in range(self.input_len)]

    def _run_circuit_inner(self, input: list[PyFelt]) -> ExtensionFieldModuloCircuit:
        circuit: final_exp.FinalExpTorusCircuit = final_exp.GaragaFinalExp[
            CurveID(self.curve_id)
        ](name="final_exp_part_1", init_hash=self.init_hash)
        t0, t1, _sum = circuit.final_exp_part1(input[0:6], input[6:12])
        # for t0_val in t0:
        #     print(f"Final exp Part1 t0 {hex(t0_val.value)}")
        # for t1_val in t1:
        #     print(f"Final exp Part1 t1 {hex(t1_val.value)}")
        # for _sum_val in _sum:
        #     print(f"Final exp Part1 _sum {hex(_sum_val.value)}")
        # Note : output is handled inside final_exp_part1.
        circuit.finalize_circuit()

        return circuit


class FinalExpPart2Circuit(BaseEXTFCircuit):
    def __init__(
        self,
        curve_id: int,
        auto_run: bool = True,
        init_hash: int = None,
        compilation_mode: int = 0,
    ):
        super().__init__(
            "final_exp_part_2", 12, curve_id, auto_run, init_hash, compilation_mode
        )

    def build_input(self) -> list[PyFelt]:
        return [self.field(randint(0, self.field.p - 1)) for _ in range(self.input_len)]

    def _run_circuit_inner(self, input: list[PyFelt]) -> ExtensionFieldModuloCircuit:
        circuit: final_exp.FinalExpTorusCircuit = final_exp.GaragaFinalExp[
            CurveID(self.curve_id)
        ](name="final_exp_part_2", hash_input=False, init_hash=self.init_hash)
        res = circuit.final_exp_finalize(input[0:6], input[6:12])
        circuit.extend_output(res)

        return circuit


class MultiMillerLoop(BaseEXTFCircuit):
    def __init__(
        self,
        curve_id: int,
        n_pairs: int = 0,
        auto_run: bool = True,
        compilation_mode: int = 0,
    ):
        self.n_pairs = n_pairs
        super().__init__(
            f"multi_miller_loop_{n_pairs}",
            6 * n_pairs,
            curve_id,
            auto_run,
            compilation_mode,
        )
        self.generic_over_curve = True

    def build_input(self) -> list[PyFelt]:
        curve_id = CurveID(self.curve_id)
        order = CURVES[self.curve_id].n
        input = []
        for _ in range(self.n_pairs):
            n1, n2 = randint(1, order), randint(1, order)
            p1, p2 = G1Point.get_nG(curve_id, n1), G2Point.get_nG(curve_id, n2)
            pair = [p1.x, p1.y, p2.x[0], p2.x[1], p2.y[0], p2.y[1]]
            input.extend([self.field(x) for x in pair])
        return input

    def _run_circuit_inner(self, input: list[PyFelt]):
        assert (
            len(input) % 6 == 0
        ), f"Input length must be a multiple of 6, got {len(input)}"
        n_pairs = len(input) // 6
        circuit = multi_miller_loop.MultiMillerLoopCircuit(
            f"multi_miller_loop_{n_pairs}",
            self.curve_id,
            n_pairs=n_pairs,
            hash_input=True,
        )
        circuit.write_p_and_q_raw(input)

        m = circuit.miller_loop(n_pairs)

        circuit.extend_output(m)
        circuit.finalize_circuit()

        return circuit


class MultiPairingCheck(BaseEXTFCircuit):
    def __init__(
        self,
        curve_id: int,
        n_pairs: int = 0,
        auto_run: bool = True,
        compilation_mode: int = 0,
    ):
        self.n_pairs = n_pairs
        super().__init__(
            f"multi_pairing_check_{n_pairs}",
            6 * n_pairs,
            curve_id,
            auto_run,
            compilation_mode,
        )
        self.generic_over_curve = True

    def build_input(self) -> list[PyFelt]:

        input, _ = multi_pairing_check.get_pairing_check_input(
            CurveID(self.curve_id), self.n_pairs
        )
        return input

    def _run_circuit_inner(self, input: list[PyFelt]):
        assert (
            len(input) % 6 == 0
        ), f"Input length must be a multiple of 6, got {len(input)}"
        n_pairs = len(input) // 6
        assert n_pairs >= 2, f"n_pairs must be >= 2, got {n_pairs}"
        circuit = multi_pairing_check.MultiPairingCheckCircuit(
            f"multi_pairing_check_{n_pairs}",
            self.curve_id,
            n_pairs=n_pairs,
            hash_input=True,
        )
        circuit.write_p_and_q_raw(input)

        m, _, _, _, _ = circuit.multi_pairing_check(n_pairs)

        circuit.extend_output(m)

        circuit.finalize_circuit()

        return circuit

class MapToCurveG2Part1Circuit(BaseModuloCircuit):
    def __init__(self, curve_id: int, compilation_mode: int = 0):
        super().__init__(
            name="map_to_curve_g2_first_step",
            curve_id=curve_id,
            compilation_mode=compilation_mode,
        )

    def build_input(self) -> list[PyFelt]:
        return [self.field(randint(0, 1000000)), self.field(0)]
    
    def _run_circuit_inner(self, input: list[PyFelt]) -> ModuloCircuit:
        circuit = MapToCurveG2(    
            self.name,
            self.curve_id,
            compilation_mode=self.compilation_mode,
        )

        circuit.set_consts()
        input_value = circuit.write_elements(input, WriteOps.INPUT)
        intermediate_values = circuit.map_to_curve_part_1(input_value)
        circuit.extend_output(intermediate_values[0]) # g1x
        circuit.extend_output(intermediate_values[1]) # div
        circuit.extend_output(intermediate_values[2]) # num_x1
        circuit.extend_output(intermediate_values[3]) # zeta_u2
        
        return circuit
    
class MapToCurveG2FinalizeQuadResCircuit(BaseModuloCircuit):
    def __init__(self, curve_id: int, compilation_mode: int = 0):
        super().__init__(
            name="map_to_curve_g2_fin_quad",
            curve_id=curve_id,
            compilation_mode=compilation_mode,
        )

    def build_input(self) -> list[PyFelt]:
        return [
            self.field(randint(0, 1000000)), # field
            self.field(0), # 0
            self.field(randint(0, 1000000)), # g1x
            self.field(0), # 0
            self.field(randint(0, 1000000)), # div
            self.field(0), # 0
            self.field(randint(0, 1000000)), # num_x1
            self.field(0), # 0
        ]
    
    def _run_circuit_inner(self, input: list[PyFelt]) -> ModuloCircuit:
        circuit = MapToCurveG2(    
            self.name,
            self.curve_id,
            compilation_mode=self.compilation_mode,
        )

        circuit.set_consts()
        field = circuit.write_elements(input[0:2], WriteOps.INPUT)
        g1x = circuit.write_elements(input[2:4], WriteOps.INPUT)
        div = circuit.write_elements(input[4:6], WriteOps.INPUT)
        num_x1 = circuit.write_elements(input[6:8], WriteOps.INPUT) 
        intermediate_values = circuit.finalize_map_to_curve_quadratic(field, g1x, div, num_x1)

        circuit.extend_output(intermediate_values[0]) # x_affine
        circuit.extend_output(intermediate_values[1]) # y_affine
        
        return circuit
    
class MapToCurveG2FinalizeNonQuadResCircuit(BaseModuloCircuit):
    def __init__(self, curve_id: int, compilation_mode: int = 0):
        super().__init__(
            name="map_to_curve_g2_fin_non_quad",
            curve_id=curve_id,
            compilation_mode=compilation_mode,
        )

    def build_input(self) -> list[PyFelt]:
        return [
            self.field(randint(0, 1000000)), # field
            self.field(0), # 0
            self.field(-2), # g1x
            self.field(-1), # 0
            self.field(randint(0, 1000000)), # div
            self.field(0), # 0
            self.field(randint(0, 1000000)), # num_x1
            self.field(0), # 0
            self.field(randint(0, 1000000)), # zeta_u2
            self.field(0), # 0
        ]
    
    def _run_circuit_inner(self, input: list[PyFelt]) -> ModuloCircuit:
        circuit = MapToCurveG2(    
            self.name,
            self.curve_id,
            compilation_mode=self.compilation_mode,
        )

        circuit.set_consts()
        field = circuit.write_elements(input[0:2], WriteOps.INPUT)
        g1x = circuit.write_elements(input[2:4], WriteOps.INPUT)
        div = circuit.write_elements(input[4:6], WriteOps.INPUT)
        num_x1 = circuit.write_elements(input[6:8], WriteOps.INPUT) 
        zeta_u2 = circuit.write_elements(input[8:10], WriteOps.INPUT)
        intermediate_values = circuit.finalize_map_to_curve_non_quadratic(field, g1x, div, num_x1, zeta_u2)

        circuit.extend_output(intermediate_values[0]) # x_affine
        circuit.extend_output(intermediate_values[1]) # y_affine
        
        return circuit
    
class IsogenyG2Circuit(BaseModuloCircuit):
    def __init__(self, curve_id: int, compilation_mode: int = 0):
        super().__init__(
            name="isogeny_g2",
            curve_id=curve_id,
            compilation_mode=compilation_mode,
        )

    def build_input(self) -> list[PyFelt]:
        return [self.field(randint(0, 1000000)), self.field(0), self.field(randint(0, 1000000)), self.field(0)]
    
    def _run_circuit_inner(self, input: list[PyFelt]) -> ModuloCircuit:
        circuit = IsogenyG2(    
            self.name,
            self.curve_id,
            compilation_mode=self.compilation_mode,
        )

        px, py = circuit.write_struct(structs.G2PointCircuit(name="pt", elmts=input))
        affine_x, affine_y = circuit.run_isogeny_g2(px, py)

        circuit.extend_struct_output(
            structs.G2PointCircuit(name="res", elmts=[affine_x[0], affine_x[1], affine_y[0], affine_y[1]])
        )