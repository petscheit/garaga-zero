%builtins range_check poseidon range_check96 add_mod mul_mod

from starkware.cairo.common.cairo_builtins import PoseidonBuiltin, ModBuiltin
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.alloc import alloc

from definitions import bls, UInt384, one_E12D, E12D
from test_utils import load_pairing_check_inputs
from bls12_381.multi_pairing_check_2 import multi_pairing_check_2P, G1G2Pair

func main{
    range_check_ptr,
    poseidon_ptr: PoseidonBuiltin*,
    range_check96_ptr: felt*,
    add_mod_ptr: ModBuiltin*,
    mul_mod_ptr: ModBuiltin*,
}() {
    alloc_locals;
    let (__fp__, _) = get_fp_and_pc();

    let n_pairs = 2;
    let curve_id = bls.CURVE_ID;

    let (local inputs: felt*) = load_pairing_check_inputs(n_pairs, curve_id);

    multi_pairing_check_2P(cast(inputs, G1G2Pair*));

    %{ print(f"Test MultiPairingCheck for {CurveID(ids.curve_id).name} and {ids.n_pairs} pairs Passed\n") %}
    return ();
}
