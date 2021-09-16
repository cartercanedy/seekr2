"""
test_analyze.py

Testing analyze.py by constructing a Smoluchowski system, for which 
analytical solutions are known. Transition times, statistics, and output 
files are generated by solutions to the Smoluchowski equation for sub-regions
of the system, and when the milestoning calculation is performed, the
results may be compared to the analytical solution to the Smoluchowski
equation.
"""

import os

import numpy as np
import pytest

import seekr2.modules.common_analyze as common_analyze
import seekr2.modules.mmvt_analyze as mmvt_analyze
import seekr2.modules.elber_analyze as elber_analyze
import seekr2.analyze as analyze
import seekr2.modules.common_base as base
import seekr2.toy.smoluchowski as smol
import seekr2.toy.toy_engine as toy_engine

def test_smoluchowski_model(smoluchowski_mmvt_model_input,
                            smoluchowski_mmvt_model):
    assert smoluchowski_mmvt_model_input.temperature == 300.0
    assert smoluchowski_mmvt_model.temperature == 300.0
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    calc = smol.make_smoluchowski_calculation_from_model(
        smoluchowski_mmvt_model, potential_energy_function)
    return

def make_smoluchowski_standard_for_k_off(mymodel, potential_energy_function):
    milestones = [mymodel.anchors[0].milestones[0].variables["radius"]]
    #if mymodel.get_type() == "mmvt":
    #    absorbing_boundary = mymodel.anchors[-1].milestones[0].variables["radius"]
    #elif mymodel.get_type() == "elber":
    #    absorbing_boundary = mymodel.anchors[-1].milestones[1].variables["radius"]
    absorbing_boundary = mymodel.anchors[-1].milestones[0].variables["radius"]
    calc = smol.SmoluchowskiCalculation1d(
        potential_energy_function, milestones=milestones, 
        absorbing_boundary=absorbing_boundary)
    
    outer_surface_flux = 4.0 * np.pi * absorbing_boundary**2 * calc.regions[1].J_outward
    w_a = calc.potential_energy_function.evaluate_energy(calc.regions[1].a)
    inner_region_height = smol.expBetaW(w_a, calc.beta)
    outer_region_height = calc.regions[1].u_r_outward[0]
    inner_region_volume = calc.regions[0].partition_function * (outer_region_height / inner_region_height)
    outer_region_volume = 1.0
    standard_time = (inner_region_volume + outer_region_volume) / outer_surface_flux    
    return standard_time

def make_smoluchowski_mmvt_analysis(mymodel, potential_energy_function, 
                                    k_on_src=None, transition_probs=None,
                                    diffusion=1.0, beta=1.0):
    calc = smol.make_smoluchowski_calculation_from_model(
        mymodel, potential_energy_function, beta=beta, diffusion=diffusion)
    my_analysis = analyze.Analysis(mymodel)
    for i, anchor in enumerate(mymodel.anchors[:-1]):
        region = calc.regions[i]
        
        N_i_j_alpha_dict, R_i_alpha_dict, N_alpha_beta_dict, new_T_alpha \
            = region.produce_mmvt_statistics(i)
            
        #print("N_alpha_beta_dict:", N_alpha_beta_dict)
        
        anchor_stats = mmvt_analyze.MMVT_anchor_statistics(alpha=i)
        anchor_stats.N_i_j_alpha = N_i_j_alpha_dict
        anchor_stats.R_i_alpha_total = R_i_alpha_dict
        anchor_stats.R_i_alpha_std_dev = R_i_alpha_dict
        anchor_stats.R_i_alpha_list = {}
        for key in anchor_stats.R_i_alpha_total:
            anchor_stats.R_i_alpha_list[key] = []
        anchor_stats.N_alpha_beta = N_alpha_beta_dict
        anchor_stats.T_alpha_total = new_T_alpha
        anchor_stats.T_alpha_std_dev = new_T_alpha
        for key in N_alpha_beta_dict:
            anchor_stats.k_alpha_beta[key] = N_alpha_beta_dict[key]

        #    N_i_j_alpha_dict, R_i_alpha_dict, N_alpha_beta_dict, new_T_alpha, 
        #    alpha=i)
        # FIll out values here...
        my_analysis.anchor_stats_list.append(anchor_stats)
    
    my_analysis.mmvt_check_anchor_stats()
    my_analysis.fill_out_data_samples()
    #my_analysis.process_data_samples()
    
    my_analysis.main_data_sample.pi_alpha = np.zeros(mymodel.num_anchors)
    my_analysis.main_data_sample.calculate_pi_alpha()
    # NOTE: the computation of k_alpha_beta, and by extension pi_alpha,
    # is flawed for the Smoluchowski method in this test suite. This
    # workaround should suffice for now, but a careful mathematical analysis
    # will need to determine the correct way to do this for the Smoluchowski
    # equation. Right now, the pi_alpha values are assigned directly based
    # on their partition functions.
    #for i, anchor in enumerate(mymodel.anchors[:-1]):
    #    region = calc.regions[i]
    #    my_analysis.main_data_sample.pi_alpha[i] = region.weight
    my_analysis.main_data_sample.fill_out_data_quantities()
    if k_on_src is not None:
        source_index = mymodel.k_on_info.bd_milestones[0].outer_milestone.index
        my_analysis.main_data_sample.b_surface_k_ons_src = {}
        my_analysis.main_data_sample.b_surface_k_ons_src[source_index] = k_on_src
        
        # transition info
        my_analysis.main_data_sample.bd_transition_probabilities[0] = transition_probs
        my_analysis.main_data_sample.bd_transition_counts[0] = transition_probs
    
    my_analysis.main_data_sample.compute_rate_matrix()
    my_analysis.main_data_sample.calculate_thermodynamics()
    my_analysis.main_data_sample.calculate_kinetics()
    mmvt_time = my_analysis.main_data_sample.MFPTs[(0,"bulk")]
    k_on = None
    if k_on_src is not None:
        k_on = my_analysis.main_data_sample.k_ons[0]
    return mmvt_time, k_on

def make_smoluchowski_elber_analysis(mymodel, potential_energy_function,
                                     k_on_src=None, transition_probs=None,
                                     diffusion=1.0, beta=1.0):
    calc = smol.make_smoluchowski_calculation_from_model(
        mymodel, potential_energy_function)
    my_analysis = analyze.Analysis(mymodel)
    
    elberN_ij, elberR_i = calc.produce_elber_statistics()
    for i, anchor in enumerate(mymodel.anchors):
        anchor_stats = elber_analyze.Elber_anchor_statistics(i)
        anchor_stats.N_i_j = {}
        for j, anchor2 in enumerate(mymodel.anchors):
            if (i, j) in elberN_ij:
                anchor_stats.N_i_j[j-i+2] = elberN_ij[(i, j)]
        anchor_stats.R_i_total = elberR_i[i]
        anchor_stats.R_i_average = elberR_i[i]
        anchor_stats.R_i_std_dev = elberR_i[i]
        anchor_stats.R_i_list = []
        my_analysis.anchor_stats_list.append(anchor_stats)
    
    my_analysis.fill_out_data_samples()
    if k_on_src is not None:
        source_index = mymodel.k_on_info.bd_milestones[0].outer_milestone.index
        my_analysis.main_data_sample.b_surface_k_ons_src = {}
        my_analysis.main_data_sample.b_surface_k_ons_src[source_index] = k_on_src
        
        # transition info
        my_analysis.main_data_sample.bd_transition_probabilities[0] = transition_probs
        my_analysis.main_data_sample.bd_transition_counts[0] = transition_probs
        
    my_analysis.main_data_sample.compute_rate_matrix()
    #self.main_data_sample.Q = common_analyze.minor2d(
    #    self.main_data_sample.Q, bulkstate, bulkstate)
    #self.main_data_sample.K = common_analyze.minor2d(
    #    self.main_data_sample.K, bulkstate, bulkstate)
    my_analysis.main_data_sample.calculate_thermodynamics()
    elberQ = np.zeros((mymodel.num_milestones, 
                       mymodel.num_milestones), dtype=np.longdouble)
    for i in range(mymodel.num_milestones):
        for j in range(mymodel.num_milestones):
            if my_analysis.main_data_sample.R_i[i] == 0.0:
                my_analysis.main_data_sample.Q[i,j] = 0.0
            else:
                my_analysis.main_data_sample.Q[i,j] \
                    = my_analysis.main_data_sample.N_ij[i,j] \
                    / my_analysis.main_data_sample.R_i[i]
                if elberR_i[i] > 0.0:
                    elberQ[i,j] = elberN_ij[i,j] / elberR_i[i]
                
    for i in range(mymodel.num_milestones):
        my_analysis.main_data_sample.Q[i][i] = \
            -np.sum(my_analysis.main_data_sample.Q[i])
        elberQ[i][i] = -np.sum(elberQ[i])
    #print("elber Q:", elberQ)
    #my_analysis.main_data_sample.Q = elberQ
    my_analysis.main_data_sample.calculate_kinetics()
    elber_time = my_analysis.main_data_sample.MFPTs[(0,"bulk")]
    k_on = None
    if k_on_src is not None:
        k_on = my_analysis.main_data_sample.k_ons[0]
    return elber_time, k_on
    
def test_smoluchowski_k_off_from_mmvt_statistics(smoluchowski_mmvt_model):
    smoluchowski_mmvt_model.k_on_info = None
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    mmvt_time, dummy = make_smoluchowski_mmvt_analysis(
        smoluchowski_mmvt_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=1e-3)
    
    potential_energy_function = smol.LinearPotentialEnergyFunction()
    mmvt_time, dummy = make_smoluchowski_mmvt_analysis(
        smoluchowski_mmvt_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=1e-3)
    
    potential_energy_function = smol.QuadraticPotentialEnergyFunction(a=0.2)
    mmvt_time, dummy = make_smoluchowski_mmvt_analysis(
        smoluchowski_mmvt_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=1e-3)
    return

def make_bd_statistics_flat(smoluchowski_model, D):
    outer_bd_radius = smoluchowski_model.k_on_info.bd_milestones[0].outer_milestone.variables["radius"]
    inner_bd_radius = smoluchowski_model.k_on_info.bd_milestones[0].inner_milestone.variables["radius"]
    inner_bd_index = smoluchowski_model.k_on_info.bd_milestones[0].inner_milestone.index
    k_on_src = 4.0 * np.pi * outer_bd_radius * D
    outward_current = 4.0 * np.pi * outer_bd_radius * D
    inward_current = 4.0 * np.pi * D / ((1.0/inner_bd_radius)-(1.0/outer_bd_radius))
    total_bd_milestone_current = outward_current + inward_current
    escape_probability = outward_current / total_bd_milestone_current
    inner_milestone_prob = inward_current / total_bd_milestone_current
    transition_probs = {inner_bd_index: inner_milestone_prob,
                        "escaped": escape_probability}
    return k_on_src, transition_probs

def make_bd_statistics_coulomb(smoluchowski_model, D, q1q2, beta):
    outer_bd_radius = smoluchowski_model.k_on_info.bd_milestones[0].outer_milestone.variables["radius"]
    inner_bd_radius = smoluchowski_model.k_on_info.bd_milestones[0].inner_milestone.variables["radius"]
    inner_bd_index = smoluchowski_model.k_on_info.bd_milestones[0].inner_milestone.index
    bound_state_radius = smoluchowski_model.anchors[0].milestones[0].variables["radius"]
    k_on_src = -q1q2 * D / (1.0 - np.exp(q1q2/(4.0*np.pi*outer_bd_radius)))
    outward_current = -q1q2 * D * np.exp(q1q2/(4.0*np.pi*outer_bd_radius)) \
        / (1.0 - np.exp(q1q2/(4.0*np.pi*outer_bd_radius)))
    inward_current = q1q2 * D * np.exp(q1q2/(4.0*np.pi*outer_bd_radius)) \
        / (np.exp(q1q2/(4.0*np.pi*inner_bd_radius)) \
        - np.exp(q1q2/(4.0*np.pi*outer_bd_radius)))
    total_bd_milestone_current = outward_current + inward_current
    escape_probability = outward_current / total_bd_milestone_current
    inner_milestone_prob = inward_current / total_bd_milestone_current
    transition_probs = {inner_bd_index: inner_milestone_prob,
                        "escaped": escape_probability}
    return k_on_src, transition_probs

def test_smoluchowski_k_on_from_mmvt_statistics(smoluchowski_mmvt_model):
    D = 1.0
    k_on_src, transition_probs = make_bd_statistics_flat(
        smoluchowski_mmvt_model, D)
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    mmvt_time, k_on = make_smoluchowski_mmvt_analysis(
        smoluchowski_mmvt_model, potential_energy_function, k_on_src, transition_probs)
    bound_state_radius = smoluchowski_mmvt_model.anchors[0].milestones[0].variables["radius"]
    standard_k_on = 4.0 * np.pi * bound_state_radius * D
    assert np.isclose(k_on, standard_k_on, rtol=1e-3)
    
    q1q2=-8.0
    beta = 1.0
    D = 1.0
    potential_energy_function = smol.CoulombicPotentialEnergyFunction(q1q2=q1q2, a=bound_state_radius)
    k_on_src, transition_probs = make_bd_statistics_coulomb(
        smoluchowski_mmvt_model, D, q1q2, beta)
    mmvt_time, k_on = make_smoluchowski_mmvt_analysis(
        smoluchowski_mmvt_model, potential_energy_function, k_on_src, transition_probs)
    
    standard_k_on = -q1q2 * D / (1.0 - np.exp(q1q2/(4.0*np.pi*bound_state_radius)))
    assert np.isclose(k_on, standard_k_on, rtol=1e-3)
    return

def test_smoluchowski_k_off_from_elber_statistics(smoluchowski_elber_model):
    smoluchowski_elber_model.k_on_info = None
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    elber_time, dummy = make_smoluchowski_elber_analysis(
        smoluchowski_elber_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_elber_model, potential_energy_function)
    assert np.isclose(elber_time, standard_time, rtol=1e-3)
    
    potential_energy_function = smol.LinearPotentialEnergyFunction()
    elber_time, dummy = make_smoluchowski_elber_analysis(
        smoluchowski_elber_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_elber_model, potential_energy_function)
    assert np.isclose(elber_time, standard_time, rtol=1e-3)
    
    potential_energy_function = smol.QuadraticPotentialEnergyFunction(a=0.2)
    elber_time, dummy = make_smoluchowski_elber_analysis(
        smoluchowski_elber_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_elber_model, potential_energy_function)
    assert np.isclose(elber_time, standard_time, rtol=1e-3)
    return

def test_smoluchowski_k_on_from_elber_statistics(smoluchowski_elber_model):
    D = 1.0
    k_on_src, transition_probs = make_bd_statistics_flat(
        smoluchowski_elber_model, D)
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    elber_time, k_on = make_smoluchowski_elber_analysis(
        smoluchowski_elber_model, potential_energy_function, k_on_src, transition_probs)
    bound_state_radius = smoluchowski_elber_model.anchors[0].milestones[0].variables["radius"]
    standard_k_on = 4.0 * np.pi * bound_state_radius * D
    assert np.isclose(k_on, standard_k_on, rtol=1e-3)
    
    q1q2=-8.0
    beta = 1.0
    D = 1.0
    potential_energy_function = smol.CoulombicPotentialEnergyFunction(q1q2=q1q2, a=bound_state_radius)
    k_on_src, transition_probs = make_bd_statistics_coulomb(
        smoluchowski_elber_model, D, q1q2, beta)
    elber_time, k_on = make_smoluchowski_elber_analysis(
        smoluchowski_elber_model, potential_energy_function, k_on_src, transition_probs)
    
    standard_k_on = -q1q2 * D / (1.0 - np.exp(q1q2/(4.0*np.pi*bound_state_radius)))
    assert np.isclose(k_on, standard_k_on, rtol=1e-3)
    return

def make_mmvt_calculation_based_on_output_files(model, potential_energy_function,
                                                k_on_src=None, transition_probs=None,
                                                style="openmm", steps=100000):
    calc = smol.make_smoluchowski_calculation_from_model(
        model, potential_energy_function)
    
    for i, anchor in enumerate(model.anchors[:-1]):
        region = calc.regions[i]
        output_file_name = os.path.join(
            model.anchor_rootdir, 
            model.anchors[i].directory,
            model.anchors[i].production_directory, "mmvt1.out")
        integrator = toy_engine.SmoluchowskiSphericalMMVTIntegrator(
            calc, i, output_file_name, style=style)
        integrator.step(steps)
    k_on = None
    if k_on_src is not None:
        highest_milestone_index = model.anchors[-1].milestones[0].index
        print("transition_probs:", transition_probs)
        b_surface_transition_probs = {"escaped": 0.9, highest_milestone_index:0.1}
        print("b_surface_transition_probs:", b_surface_transition_probs)
        b_surface_output_file_name = os.path.join(
            model.anchor_rootdir, 
            model.k_on_info.b_surface_directory, "results1.xml")
        toy_engine.write_b_surface_output_file(
            b_surface_output_file_name, k_on_src*10.0, 
            b_surface_transition_probs, transition_probs)
        
        # TODO: remove because uses old BD milestone method
        #bd_milestone_output_file_name = os.path.join(
        #    model.anchor_rootdir, 
        #    model.k_on_info.bd_milestones[0].directory, "results.xml")
        #toy_engine.write_b_surface_output_file(
        #    bd_milestone_output_file_name, k_on_src, transition_probs)
    
    my_analysis = analyze.analyze(model, num_error_samples=10)
    mmvt_time = my_analysis.main_data_sample.MFPTs[(0,"bulk")]
    if k_on_src is not None:
        k_on = my_analysis.main_data_sample.k_ons[0]
    
    my_analysis.print_results()
    image_directory = common_analyze.make_image_directory(model, None)
    my_analysis.save_plots(os.path.join(model.anchor_rootdir, image_directory))
    return mmvt_time, k_on

def test_smoluchowski_k_off_from_mmvt_openmm_output_files(smoluchowski_mmvt_model):
    smoluchowski_mmvt_model.openmm_settings = base.Openmm_settings()
    smoluchowski_mmvt_model.openmm_settings.langevin_integrator = base.Langevin_integrator_settings()
    smoluchowski_mmvt_model.k_on_info = None
    
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    mmvt_time, dummy = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=2e-1)
    
    potential_energy_function = smol.LinearPotentialEnergyFunction()
    mmvt_time, dummy = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=2e-1)
    
    potential_energy_function = smol.QuadraticPotentialEnergyFunction(a=0.1)
    mmvt_time, dummy = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=2e-1)
    return
    
def test_smoluchowski_k_off_from_mmvt_namd_output_files(smoluchowski_mmvt_model):
    smoluchowski_mmvt_model.namd_settings = base.Namd_settings()
    smoluchowski_mmvt_model.namd_settings.langevin_integrator = base.Langevin_integrator_settings()
    smoluchowski_mmvt_model.k_on_info = None
    
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    mmvt_time, dummy = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function, style="namd")
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=2e-1)
    
    potential_energy_function = smol.LinearPotentialEnergyFunction()
    mmvt_time, dummy = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function, style="namd")
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=2e-1)
    
    potential_energy_function = smol.QuadraticPotentialEnergyFunction(a=0.1)
    mmvt_time, dummy = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function, style="namd")
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_mmvt_model, potential_energy_function)
    assert np.isclose(mmvt_time, standard_time, rtol=2e-1)
    return

def test_smoluchowski_k_on_from_mmvt_openmm_output_files(smoluchowski_mmvt_model):
    smoluchowski_mmvt_model.openmm_settings = base.Openmm_settings()
    smoluchowski_mmvt_model.openmm_settings.langevin_integrator = base.Langevin_integrator_settings()
    D = 1.0
    b_surface_dir_path = os.path.join(
        smoluchowski_mmvt_model.anchor_rootdir, 
        smoluchowski_mmvt_model.k_on_info.b_surface_directory)
    os.mkdir(b_surface_dir_path)
    k_on_src, transition_probs = make_bd_statistics_flat(
        smoluchowski_mmvt_model, D)
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    mmvt_time, k_on = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function, k_on_src, transition_probs)
    bound_state_radius = smoluchowski_mmvt_model.anchors[0].milestones[0].variables["radius"]
    standard_k_on = 4.0 * np.pi * bound_state_radius * D
    assert np.isclose(k_on, standard_k_on, rtol=2e-1)
    
    q1q2=-8.0
    beta = 1.0
    D = 1.0
    
    potential_energy_function = smol.CoulombicPotentialEnergyFunction(q1q2=q1q2, a=bound_state_radius)
    k_on_src, transition_probs = make_bd_statistics_coulomb(
        smoluchowski_mmvt_model, D, q1q2, beta)
    mmvt_time, k_on = make_mmvt_calculation_based_on_output_files(
        smoluchowski_mmvt_model, potential_energy_function, k_on_src, transition_probs)
    bound_state_radius = smoluchowski_mmvt_model.anchors[0].milestones[0].variables["radius"]
    standard_k_on = -q1q2 * D / (1.0 - np.exp(q1q2/(4.0*np.pi*bound_state_radius)))
    assert np.isclose(k_on, standard_k_on, rtol=3e-1)
    return

def make_elber_calculation_based_on_output_files(model, potential_energy_function,
                                                k_on_src=None, transition_probs=None,
                                                steps=100000):
    calc = smol.make_smoluchowski_calculation_from_model(
        model, potential_energy_function)
    
    for i, anchor in enumerate(model.anchors[:-1]):
        region = calc.regions[i]
        output_file_name = os.path.join(
            model.anchor_rootdir, 
            model.anchors[i].directory,
            model.anchors[i].production_directory, "forward1.out")
        
        integrator = toy_engine.SmoluchowskiSphericalElberIntegrator(
            calc, i, output_file_name)
        integrator.step(steps)
    
    k_on = None
    if k_on_src is not None:
        highest_milestone_index = model.k_on_info.bd_milestones[0].outer_milestone.index
        b_surface_transition_probs = {"escaped": 0.9, highest_milestone_index:0.1}
        b_surface_output_file_name = os.path.join(
            model.anchor_rootdir, 
            model.k_on_info.b_surface_directory, "results1.xml")
        toy_engine.write_b_surface_output_file(
            b_surface_output_file_name, k_on_src*10.0, 
            b_surface_transition_probs, transition_probs)
        
        """
        bd_milestone_output_file_name = os.path.join(
            model.anchor_rootdir, 
            model.k_on_info.bd_milestones[0].directory, "results.xml")
        toy_engine.write_b_surface_output_file(
            bd_milestone_output_file_name, k_on_src, transition_probs)
        """
    
    my_analysis = analyze.analyze(model, num_error_samples=10)
    elber_time = my_analysis.main_data_sample.MFPTs[(0,"bulk")]
    if k_on_src is not None:
        k_on = my_analysis.main_data_sample.k_ons[0]
    
    return elber_time, k_on

def test_smoluchowski_k_off_from_elber_openmm_output_files(smoluchowski_elber_model):
    smoluchowski_elber_model.openmm_settings = base.Openmm_settings()
    smoluchowski_elber_model.openmm_settings.langevin_integrator = base.Langevin_integrator_settings()
    smoluchowski_elber_model.k_on_info = None
    
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    elber_time, dummy = make_elber_calculation_based_on_output_files(
        smoluchowski_elber_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_elber_model, potential_energy_function)
    assert np.isclose(elber_time, standard_time, rtol=2e-1)
    
    potential_energy_function = smol.LinearPotentialEnergyFunction()
    elber_time, dummy = make_elber_calculation_based_on_output_files(
        smoluchowski_elber_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_elber_model, potential_energy_function)
    assert np.isclose(elber_time, standard_time, rtol=2e-1)
    
    potential_energy_function = smol.QuadraticPotentialEnergyFunction(a=0.1)
    elber_time, dummy = make_elber_calculation_based_on_output_files(
        smoluchowski_elber_model, potential_energy_function)
    standard_time = make_smoluchowski_standard_for_k_off(
        smoluchowski_elber_model, potential_energy_function)
    assert np.isclose(elber_time, standard_time, rtol=2e-1)
    return

def test_smoluchowski_k_on_from_elber_openmm_output_files(smoluchowski_elber_model):
    smoluchowski_elber_model.openmm_settings = base.Openmm_settings()
    smoluchowski_elber_model.openmm_settings.langevin_integrator = base.Langevin_integrator_settings()
    D = 1.0
    b_surface_dir_path = os.path.join(
        smoluchowski_elber_model.anchor_rootdir, 
        smoluchowski_elber_model.k_on_info.b_surface_directory)
    os.mkdir(b_surface_dir_path)
    k_on_src, transition_probs = make_bd_statistics_flat(
        smoluchowski_elber_model, D)
    potential_energy_function = smol.FlatPotentialEnergyFunction()
    mmvt_time, k_on = make_elber_calculation_based_on_output_files(
        smoluchowski_elber_model, potential_energy_function, k_on_src, transition_probs)
    bound_state_radius = smoluchowski_elber_model.anchors[0].milestones[0].variables["radius"]
    standard_k_on = 4.0 * np.pi * bound_state_radius * D
    assert np.isclose(k_on, standard_k_on, rtol=2e-1)
    
    q1q2=-8.0
    beta = 1.0
    D = 1.0
    
    potential_energy_function = smol.CoulombicPotentialEnergyFunction(q1q2=q1q2, a=bound_state_radius)
    k_on_src, transition_probs = make_bd_statistics_coulomb(
        smoluchowski_elber_model, D, q1q2, beta)
    mmvt_time, k_on = make_elber_calculation_based_on_output_files(
        smoluchowski_elber_model, potential_energy_function, k_on_src, transition_probs)
    bound_state_radius = smoluchowski_elber_model.anchors[0].milestones[0].variables["radius"]
    standard_k_on = -q1q2 * D / (1.0 - np.exp(q1q2/(4.0*np.pi*bound_state_radius)))
    assert np.isclose(k_on, standard_k_on, rtol=3e-1)
    return
