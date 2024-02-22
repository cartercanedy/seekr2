"""
Structures, methods, and functions for handling Spherical CVs.
(COM-COM distance CV).
"""

import numpy as np

from parmed import unit

import seekr2.modules.common_base as base
import seekr2.modules.mmvt_cvs.mmvt_cv_base as mmvt_cv_base
from seekr2.modules.mmvt_cvs.mmvt_cv_base import MMVT_collective_variable

class MMVT_planar_CV(MMVT_collective_variable):
    """
    A planar incremental variable represents the distance between two
    different groups of atoms.
    
    """+MMVT_collective_variable.__doc__
    
    def __init__(self, index, start_group, end_group, mobile_group):
        self.index = index
        self.start_group = start_group
        self.end_group = end_group
        self.mobile_group = mobile_group
        self.name = "mmvt_planar"
        self.openmm_expression = "step(k*("\
            "((x2-x1)*(x3-x1) + (y2-y1)*(y3-y1) + (z2-z1)*(z3-z1))"\
            "/ (distance(g1, g2)*distance(g1, g2)) - value))"
        self.restraining_expression = "k*("\
            "((x2-x1)*(x3-x1) + (y2-y1)*(y3-y1) + (z2-z1)*(z3-z1))"\
            "/ (distance(g1, g2)*distance(g1, g2)) - value)^2"
        self.cv_expression \
            = "((x2-x1)*(x3-x1) + (y2-y1)*(y3-y1) + (z2-z1)*(z3-z1))"\
            "/ (distance(g1, g2)*distance(g1, g2))"
        self.num_groups = 3
        self.per_dof_variables = ["k", "value"]
        self.global_variables = []
        self._mygroup_list = None
        self.variable_name = "v"
        return

    def __name__(self):
        return "MMVT_planar_CV"
    
    def make_boundary_force(self, alias_id):
        """
        Create an OpenMM force object which will be used to compute
        the value of the CV's mathematical expression as the simulation
        propagates. Each *milestone* in a cell, not each CV, will have
        a force object created.
        
        In this implementation of MMVT in OpenMM, CustomForce objects
        are used to provide the boundary definitions of the MMVT cell.
        These 'forces' are designed to never affect atomic motions,
        but are merely monitored by the plugin for bouncing event.
        So while they are technically OpenMM force objects, we don't
        refer to them as forces outside of this layer of the code,
        preferring instead the term: boundary definitions.
        """
        try:
            import openmm
        except ImportError:
            import simtk.openmm as openmm
            
        assert self.num_groups == 3
        expression_w_bitcode = "bitcode*"+self.openmm_expression
        return openmm.CustomCentroidBondForce(
            self.num_groups, expression_w_bitcode)
    
    def make_restraining_force(self, alias_id):
        """
        Create an OpenMM force object that will restrain the system to
        a given value of this CV.
        """
        try:
            import openmm
        except ImportError:
            import simtk.openmm as openmm
            
        assert self.num_groups == 3
        return openmm.CustomCentroidBondForce(
            self.num_groups, self.restraining_expression)
    
    def make_cv_force(self, alias_id):
        try:
            import openmm
        except ImportError:
            import simtk.openmm as openmm
        return openmm.CustomCentroidBondForce(
            self.num_groups, self.cv_expression)
    
    def make_voronoi_cv_boundary_forces(self, me_val, neighbor_val, alias_id):
        """
        
        """
        try:
            import openmm
        except ImportError:
            import simtk.openmm as openmm
            
        me_expr = "(me_val - {})^2".format(self.cv_expression)
        me_force = openmm.CustomCentroidBondForce(
            self.num_groups, me_expr)
        megroup1 = me_force.addGroup(self.start_group)
        megroup2 = me_force.addGroup(self.end_group)
        megroup3 = me_force.addGroup(self.mobile_group)
        me_force.addPerBondParameter("me_val")
        me_force.addBond([megroup1, megroup2, megroup3], [me_val])
        
        neighbor_expr = "(neighbor_val - {})^2".format(self.cv_expression)
        neighbor_force = openmm.CustomCentroidBondForce(
            self.num_groups, neighbor_expr)
        neighborgroup1 = neighbor_force.addGroup(self.start_group)
        neighborgroup2 = neighbor_force.addGroup(self.end_group)
        neighborgroup3 = neighbor_force.addGroup(self.mobile_group)
        neighbor_force.addPerBondParameter("neighbor_val")
        neighbor_force.addBond(
            [neighborgroup1, neighborgroup2, neighborgroup3], [neighbor_val])
        
        return me_force, neighbor_force
    
    def update_voronoi_cv_boundary_forces(
            self, me_force, me_val, neighbor_force, neighbor_val, alias_id,
            context):
        """
        
        """
        # the group list values of [0,1] is hacky, but probably correct
        me_force.setBondParameters(0, [0,1,2], [me_val])
        neighbor_force.setBondParameters(0, [0,1,2], [neighbor_val])
        return
    
    def make_namd_colvar_string(self):
        """
        This string will be put into a NAMD colvar file for tracking
        MMVT bounces.
        """
        raise Exception("MMVT Planar CVs are not available in NAMD")
    
    def add_groups(self, force):
        """
        
        """
        self._mygroup_list = []
        mygroup1 = force.addGroup(self.start_group)
        self._mygroup_list.append(mygroup1)
        mygroup2 = force.addGroup(self.end_group)
        self._mygroup_list.append(mygroup2)
        mygroup3 = force.addGroup(self.mobile_group)
        self._mygroup_list.append(mygroup3)
        return
    
    def add_parameters(self, force):
        """
        An OpenMM custom force object needs a list of variables
        provided to it that will occur within its expression. Both
        the per-dof and global variables are combined within the
        variable_names_list. The numerical values of these variables
        will be provided at a later step.
        """
        self.add_groups(force)
        variable_names_list = []
        variable_names_list.append("bitcode")
        force.addPerBondParameter("bitcode")
        if self.per_dof_variables is not None:
            for per_dof_variable in self.per_dof_variables:
                force.addPerBondParameter(per_dof_variable)
                variable_names_list.append(per_dof_variable)
        
        if self.global_variables is not None:
            for global_variable in self.global_variables:
                force.addGlobalParameter(global_variable)
                variable_names_list.append(global_variable)
        
        return variable_names_list
    
    def add_groups_and_variables(self, force, variables, alias_id):
        """
        Provide the custom force with additional information it needs,
        which includes a list of the groups of atoms involved with the
        CV, as well as a list of the variables' *values*.
        """
        assert len(self._mygroup_list) == self.num_groups
        force.addBond(self._mygroup_list, variables)
        return
    
    def update_groups_and_variables(self, force, variables, alias_id, context):
        """
        Update the force's variables with a list of new values.
        """
        force.setBondParameters(0, self._mygroup_list, variables)
        return
    
    def get_variable_values_list(self, milestone):
        """
        Create the list of CV variables' values in the proper order
        so they can be provided to the custom force object.
        """
        assert milestone.cv_index == self.index
        values_list = []
        bitcode = 2**(milestone.alias_index-1)
        k = milestone.variables["k"] * unit.kilojoules_per_mole/unit.angstrom**2
        value = milestone.variables["value"] * unit.nanometers
        values_list.append(bitcode)
        values_list.append(k)
        values_list.append(value)
        return values_list
    
    def get_namd_evaluation_string(self, milestone, cv_val_var="cv_val"):
        """
        For a given milestone, return a string that can be evaluated
        my NAMD to monitor for a crossing event. Essentially, if the 
        function defined by the string ever returns True, then a
        bounce will occur
        """
        raise Exception("MMVT Planar CVs are not available in NAMD")
    
    def get_mdtraj_cv_value(self, traj, frame_index):
        """
        Determine the current CV value for an mdtraj object.
        """
        traj1 = traj.atom_slice(self.start_group)
        traj2 = traj.atom_slice(self.end_group)
        traj3 = traj.atom_slice(self.mobile_group)
        com1_array = mmvt_cv_base.traj_center_of_mass(traj1)
        com2_array = mmvt_cv_base.traj_center_of_mass(traj2)
        com3_array = mmvt_cv_base.traj_center_of_mass(traj3)
        #com1_array = mdtraj.compute_center_of_mass(traj1)
        #com2_array = mdtraj.compute_center_of_mass(traj2)
        #com3_array = mdtraj.compute_center_of_mass(traj3)
        com1 = com1_array[frame_index,:]
        com2 = com2_array[frame_index,:]
        com3 = com3_array[frame_index,:]
        dist1_2 = np.linalg.norm(com2-com1)
        #dist1_3 = np.linalg.norm(com3-com1)
        value = ((com2[0]-com1[0])*(com3[0]-com1[0]) \
               + (com2[1]-com1[1])*(com3[1]-com1[1]) \
               + (com2[2]-com1[2])*(com3[2]-com1[2]))/(dist1_2*dist1_2)
        return value
    
    def check_mdtraj_within_boundary(self, traj, milestone_variables, 
                                     verbose=False, TOL=0.001):
        """
        Check if an mdtraj Trajectory describes a system that remains
        within the expected anchor. Return True if passed, return
        False if failed.
        """
        for frame_index in range(traj.n_frames):
            value = self.get_mdtraj_cv_value(traj, frame_index)
            result = self.check_value_within_boundary(
                value, milestone_variables, verbose=verbose, tolerance=TOL)
            if not result:
                return False
            
        return True
    
    def get_openmm_context_cv_value(self, context, positions=None, system=None):
        """
        Determine the current CV value for an openmm context.
        """
        if system is None:
            system = context.getSystem()
        if positions is None:
            state = context.getState(getPositions=True)
            positions = state.getPositions()
        com1 = base.get_openmm_center_of_mass_com(
            system, positions, self.start_group)
        com2 = base.get_openmm_center_of_mass_com(
            system, positions, self.end_group)
        com3 = base.get_openmm_center_of_mass_com(
            system, positions, self.mobile_group)
        dist1_2 = np.linalg.norm(com2-com1)
        #dist1_3 = np.linalg.norm(com3-com1)
        value = ((com2[0]-com1[0])*(com3[0]-com1[0]) \
               + (com2[1]-com1[1])*(com3[1]-com1[1]) \
               + (com2[2]-com1[2])*(com3[2]-com1[2]))/(dist1_2*dist1_2)
        return value.value_in_unit(unit.nanometers**2)
        #return value
        
    def check_openmm_context_within_boundary(
            self, context, milestone_variables, positions=None, verbose=False,
            tolerance=0.0):
        """
        Check if an OpenMM context describes a system that remains
        within the expected anchor. Return True if passed, return
        False if failed.
        """
        value = self.get_openmm_context_cv_value(context, positions)
        result = self.check_value_within_boundary(
            value, milestone_variables, verbose, tolerance)
        return result
    
    def check_value_within_boundary(self, value, milestone_variables, 
                                    verbose=False, tolerance=0.0):
        milestone_k = milestone_variables["k"]
        milestone_value = milestone_variables["value"]
        if milestone_k*(value - milestone_value) > tolerance:
            if verbose:
                warnstr = """The value of planar milestone was found to be 
{:.4f}. This distance falls outside of the milestoneboundary at {:.4f}.
""".format(value, milestone_value)
                print(warnstr)
            return False
        return True
    
    def check_mdtraj_close_to_boundary(self, traj, milestone_variables, 
                                     verbose=False, max_avg=0.03, max_std=0.05):
        """
        Given an mdtraj Trajectory, check if the system lies close
        to the MMVT boundary. Return True if passed, return False if 
        failed.
        """
        values = []
        for frame_index in range(traj.n_frames):
            value = self.get_mdtraj_cv_value(traj, frame_index)
            milestone_value = milestone_variables["value"]
            values.append(value - milestone_value)
            
        avg_distance = np.mean(values)
        std_distance = np.std(values)
        if abs(avg_distance) > max_avg or std_distance > max_std:
            if verbose:
                warnstr = """The distance between the system and central 
    milestone were found on average to be {:.4f} apart.
    The standard deviation was {:.4f}.""".format(avg_distance, std_distance)
                print(warnstr)
            return False
            
        return True
    
    def get_atom_groups(self):
        """
        Return a 3-list of this CV's atomic groups.
        """
        return [self.start_group, self.end_group, self.mobile_group]
            
    def get_variable_values(self):
        """
        This type of CV has no extra variables, so an empty list is 
        returned.
        """
        return []

def make_mmvt_planar_cv_object(planar_cv_input, index):
    """
    Create a PlanarCV object to be placed into the Model.
    """
    start_group = base.parse_xml_list(planar_cv_input.start_group)
    end_group = base.parse_xml_list(planar_cv_input.end_group)
    mobile_group = base.parse_xml_list(planar_cv_input.mobile_group)
    cv = MMVT_planar_CV(index, start_group, end_group, mobile_group)
    return cv
