"""
Run entire SEEKR2 calculations to test for problems in the 
pipeline.
"""
import os
import sys
import time
import tempfile

import seekr2.tests.create_model_input as create_model_input
import seekr2.prepare as prepare
import seekr2.modules.check as check
import seekr2.run as run
import seekr2.converge as converge
import seekr2.modules.common_converge as common_converge
import seekr2.analyze as analyze
from seekr2.modules.common_prepare import Browndye_settings_input, \
    MMVT_input_settings, Elber_input_settings
from seekr2.modules.common_base import Ion, Amber_params, Forcefield_params, \
    Box_vectors
from seekr2.modules.common_cv import Spherical_cv_anchor, Spherical_cv_input

def run_short_ci(model_input, cuda_device_index, long_check=True):
    start_dir = os.getcwd()
    model, xml_path = prepare.generate_seekr2_model_and_filetree(
        model_input, force_overwrite=False)
    
    model_dir = os.path.dirname(xml_path)
    model.anchor_rootdir = os.path.abspath(model_dir)
    check.check_pre_simulation_all(model)
    run.run(model, "any", min_b_surface_simulation_length=1000,
            num_rev_launches=10, cuda_device_index=cuda_device_index,
            save_state_file=True)
    data_sample_list = converge.converge(model, k_on_state=0)
    rmsd_convergence_results = common_converge.calc_RMSD_conv_amount(
        model, data_sample_list)
    transition_minima, transition_details, transition_times \
        = common_converge.calc_transition_steps(
        model, data_sample_list[-1])
    converge.print_convergence_results(
        model, rmsd_convergence_results, cutoff=0.1, 
        transition_results=transition_details, 
        transition_time_results=transition_times,
        minimum_anchor_transitions=10, 
        bd_transition_counts=data_sample_list[-1].bd_transition_counts)
    check.check_post_simulation_all(model, long_check=long_check)
    analysis = analyze.analyze(model)
    analysis.print_results()
    os.chdir(start_dir)
    return

def run_generic_hostguest_ci(cuda_device_index):
    with tempfile.TemporaryDirectory() as temp_dir:
        host_guest_model_input \
            = create_model_input.create_host_guest_mmvt_model_input(temp_dir)
        run_short_ci(host_guest_model_input, cuda_device_index)
        
    return

def run_generic_namd_hostguest_ci(cuda_device_index):
    with tempfile.TemporaryDirectory() as temp_dir:
        host_guest_model_input \
            = create_model_input.create_host_guest_mmvt_model_input(temp_dir)
        host_guest_model_input.md_program = "namd"
        for input_anchor in host_guest_model_input.cv_inputs[0].input_anchors:
            input_anchor.starting_amber_params.prmtop_filename \
                = "../data/hostguest_files/hostguest_for_NAMD.parm7"
        run_short_ci(host_guest_model_input, cuda_device_index, 
                     long_check=False)
        
    return

def run_elber_hostguest_ci(cuda_device_index):
    with tempfile.TemporaryDirectory() as temp_dir:
        host_guest_model_input \
            = create_model_input.create_host_guest_elber_model_input(temp_dir)
        run_short_ci(host_guest_model_input, cuda_device_index,
                     long_check=False)
        host_guest_model_input.calculation_type = "elber"
        
    return

def run_multisite_sod_ci(cuda_device_index):
    with tempfile.TemporaryDirectory() as temp_dir:
        sod_model_input \
            = create_model_input.create_sod_mmvt_model_input(temp_dir)
        run_short_ci(sod_model_input, cuda_device_index, long_check=False)
        
    return

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        argument = "short"
    else:
        argument = sys.argv[1]
        
    if len(sys.argv) == 3:
        cuda_device_index = sys.argv[2]
    else:
        cuda_device_index = None
    
    starttime = time.time()
    if argument == "short":
        run_generic_hostguest_ci(cuda_device_index)
    elif argument == "namd":
        run_generic_namd_hostguest_ci(cuda_device_index)
    elif argument == "elber":
        run_elber_hostguest_ci(cuda_device_index)
    elif argument == "multisite":
        run_multisite_sod_ci(cuda_device_index)
    elif argument == "long":
        run_generic_hostguest_ci(cuda_device_index)
        run_generic_namd_hostguest_ci(cuda_device_index)
        run_elber_hostguest_ci(cuda_device_index)
        run_multisite_sod_ci(cuda_device_index)
        
    print("Time elapsed: {:.3f}".format(time.time() - starttime))
    print("Continuous Integration Tests Passed Successfully.")