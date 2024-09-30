%builtins range_check poseidon range_check96 add_mod mul_mod

// from starkware.cairo.common.cairo_builtins import UInt384
from starkware.cairo.common.cairo_builtins import PoseidonBuiltin, ModBuiltin
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.alloc import alloc

from definitions import bn, bls, UInt384, one_E12D, N_LIMBS, BASE, E12D, G1Point, G2Point, G1G2Pair

from pairing import multi_pairing
from modulo_circuit import ExtensionFieldModuloCircuit

func main{
    range_check_ptr,
    poseidon_ptr: PoseidonBuiltin*,
    range_check96_ptr: felt*,
    add_mod_ptr: ModBuiltin*,
    mul_mod_ptr: ModBuiltin*,
}() {
    alloc_locals;
    %{ print("starting...") %}
    let g1_neg_sig_pair = G1G2Pair(
        P=G1Point(
            x=UInt384(
                77209383603911340680728987323,
                49921657856232494206459177023,
                24654436777218005952848247045,
                7410505851925769877053596556
            ),
            y=UInt384(
                4578755106311036904654095050,
                31671107278004379566943975610,
                64119167930385062737200089033,
                5354471328347505754258634440
            )
        ),
        Q=G2Point(
            x0=UInt384(
                55676019058802805716531268775,
                30891190235243100842850062539,
                8277615870342056232923415400,
                5464564657489375345690573078
            ),
            x1=UInt384(
                7307445816014068279126343269,
                26722620361016783735625000676,
                5125074513475745601000079093,
                6526305679697766371433464129
            ),
            y0=UInt384(
                43127343288069052441481880137,
                22971473186588520506471026051,
                61929595200232768831988208553,
                6011026918429864945082946484
            ),
            y1=UInt384(
                74607609643801153667754747514,
                8931632023021527859249747249,
                46455715815241382932844578362,
                732461856662282362885016752
            ),
        ),
    );

    let pk_msg_pair = G1G2Pair(
        P=G1Point(
            x=UInt384(
                5170378098107523586082636473,
                885616833454868841647409485,
                50076641190128282704423923524,
                3936401618834000089796178733
            ),
            y=UInt384(
                18576093918100221948595919837,
                11259731807595477526632380055,
                65260189484196126616995484322,
                677757701214493964412485362
            ),
        ),
        Q=G2Point(
            x0=UInt384(61749095370833073208483023492, 41284159994856811920526353, 76400070978001749850783996079, 4779257898238134090961237862),
            x1=UInt384(52085968068846222712265618411, 25615398918813555460167082637, 51946016755646804223737100752, 2425343964792420405424081588),
            y0=UInt384(37730344162885648145253876097, 8769524215769261497871301147, 31408813748588110380958221919, 2209127891331474752520569998),
            y1=UInt384(6350568244597509393535966077, 32382964280741628563649345392, 46113357445723640894033411436, 1967452402116889754788140757),
        ),
    );

    let (inputs: G1G2Pair*) = alloc();
    assert inputs[0] = g1_neg_sig_pair;
    assert inputs[1] = pk_msg_pair;
    %{ print("done allocating") %}

    let (res) = multi_pairing(inputs, 2, 1);
    %{
        print("res0: ", ids.res.w0.d0)
        print("res1: ", ids.res.w0.d1)
        print("res2: ", ids.res.w0.d2)
        print("res3: ", ids.res.w0.d3)
    %}
    let (one) = one_E12D();
    %{
        print("one0: ", ids.one.w0.d0)
        print("one1: ", ids.one.w0.d1)
        print("one2: ", ids.one.w0.d2)
        print("one3: ", ids.one.w0.d3)
    %}
    assert res = one;
    %{ print("done pairing. Success!") %}

    return ();
}

