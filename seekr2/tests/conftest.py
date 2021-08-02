"""
conftest.py

configurations for all tests
"""

import os
import tempfile
import pytest
import copy

import numpy as np

import seekr2.prepare as prepare
import seekr2.modules.common_base as base
import seekr2.tests.create_model_input as create_model_input

TEST_DIRECTORY = os.path.dirname(__file__)

@pytest.fixture(scope="session")
def host_guest_mmvt_model_input_persistent(tmpdir_factory):
    """
    Create a model object that is persistent across the tests in this file.
    """
    rootdir = tmpdir_factory.mktemp("hostguest_mmvt")
    host_guest_mmvt_model_input_persisent_obj \
        = create_model_input.create_host_guest_mmvt_model_input(
            rootdir, bd=True)
    return host_guest_mmvt_model_input_persisent_obj

@pytest.fixture()
def host_guest_mmvt_model_input(host_guest_mmvt_model_input_persistent):
    """
    Create a copy of the model input that is not persistent. But this 
    at least doesn't require us to generate an entirely new model 
    input.
    """
    host_guest_mmvt_model_input_obj = copy.deepcopy(
        host_guest_mmvt_model_input_persistent)
    return host_guest_mmvt_model_input_obj

@pytest.fixture(scope="session")
def host_guest_mmvt_model_persistent(tmpdir_factory, 
                                     host_guest_model_input_persistent):
    """
    Create a model object that is persistent across the tests in this file.
    """
    os.chdir(TEST_DIRECTORY)
    host_guest_mmvt_model_obj, model_xml_path \
        = prepare.generate_seekr2_model_and_filetree(
            host_guest_mmvt_model_input_persistent, force_overwrite=False)
    model_dir = os.path.dirname(model_xml_path)
    host_guest_mmvt_model_obj.anchor_rootdir = os.path.abspath(model_dir)
    return host_guest_mmvt_model_obj

@pytest.fixture
def host_guest_mmvt_model(tmpdir_factory, host_guest_mmvt_model_persistent):
    """
    Create a copy of the model that is not persistent. But this at least
    doesn't require us to generate an entirely new model
    """
    host_guest_mmvt_model = copy.deepcopy(host_guest_mmvt_model_persistent)
    return host_guest_mmvt_model

@pytest.fixture(scope="session")
def tryp_ben_mmvt_model_input_persistent(tmpdir_factory):
    """
    Create a model object that is persistent across the tests in this file.
    """
    rootdir = tmpdir_factory.mktemp("tryp_ben_mmvt")
    tryp_ben_mmvt_model_input_persistent_obj \
        = create_model_input.create_tryp_ben_mmvt_model_input(
            rootdir, bd=True)
    return tryp_ben_mmvt_model_input_persistent_obj

@pytest.fixture()
def tryp_ben_mmvt_model_input(tmpdir_factory, 
                              tryp_ben_mmvt_model_input_persistent):
    """
    Create a copy of the model input that is not persistent. But this 
    at least doesn't require us to generate an entirely new model 
    input.
    """
    tryp_ben_mmvt_model_input_obj = copy.deepcopy(
        tryp_ben_mmvt_model_input_persistent)
    return tryp_ben_mmvt_model_input_obj

@pytest.fixture(scope="session")
def tryp_ben_mmvt_model_persistent(tmpdir_factory, 
                                   tryp_ben_mmvt_model_input_persistent):
    """
    Create a model object that is persistent across the tests in this file.
    """
    os.chdir(TEST_DIRECTORY)
    #print("mmvt curdir:", os.getcwd())
    tryp_ben_mmvt_model_obj, model_xml_path \
        = prepare.generate_seekr2_model_and_filetree(
            tryp_ben_mmvt_model_input_persistent, force_overwrite=False)
    model_dir = os.path.dirname(model_xml_path)
    tryp_ben_mmvt_model_obj.anchor_rootdir = os.path.abspath(model_dir)
    return tryp_ben_mmvt_model_obj

@pytest.fixture
def tryp_ben_mmvt_model(tmpdir_factory, tryp_ben_mmvt_model_persistent):
    """
    Create a copy of the model that is not persistent. But this at least
    doesn't require us to generate an entirely new model
    """
    tryp_ben_mmvt_model_obj = copy.deepcopy(tryp_ben_mmvt_model_persistent)
    return tryp_ben_mmvt_model_obj

@pytest.fixture(scope="session")
def tryp_ben_elber_model_input_persistent(tmpdir_factory):
    """
    Create a model object that is persistent across the tests in this file.
    """
    rootdir = tmpdir_factory.mktemp("tryp_ben_elber")
    tryp_ben_elber_model_input_persistent_obj \
        = create_model_input.create_tryp_ben_elber_model_input(
            rootdir, bd=False)
    return tryp_ben_elber_model_input_persistent_obj

@pytest.fixture(scope="session")
def tryp_ben_elber_model_persistent(tmpdir_factory, 
                                   tryp_ben_elber_model_input_persistent):
    """
    Create a model object that is persistent across the tests in this file.
    """
    os.chdir(TEST_DIRECTORY)
    #print("elber curdir:", os.getcwd())
    tryp_ben_elber_model_obj, model_xml_path \
        = prepare.generate_seekr2_model_and_filetree(
            tryp_ben_elber_model_input_persistent, force_overwrite=False)
    model_dir = os.path.dirname(model_xml_path)
    tryp_ben_elber_model_obj.anchor_rootdir = os.path.abspath(model_dir)
    return tryp_ben_elber_model_obj

@pytest.fixture
def tryp_ben_elber_model(tmpdir_factory, tryp_ben_elber_model_persistent):
    """
    Create a copy of the model that is not persistent. But this at least
    doesn't require us to generate an entirely new model
    """
    tryp_ben_elber_model_obj = copy.deepcopy(tryp_ben_elber_model_persistent)
    return tryp_ben_elber_model_obj

@pytest.fixture(scope="session")
def smoluchowski_mmvt_model_input_persistent(tmpdir_factory):
    """
    Create a model object that is persistent across the tests in this file.
    """
    rootdir = tmpdir_factory.mktemp("smoluchowski_mmvt")
    smoluchowski_mmvt_model_input_persisent_obj \
        = create_model_input.create_smoluchowski_mmvt_model_input(
            rootdir)
    return smoluchowski_mmvt_model_input_persisent_obj

@pytest.fixture()
def smoluchowski_mmvt_model_input(smoluchowski_mmvt_model_input_persistent):
    """
    Create a copy of the model input that is not persistent. But this 
    at least doesn't require us to generate an entirely new model 
    input.
    """
    smoluchowski_mmvt_model_input_obj = copy.deepcopy(
        smoluchowski_mmvt_model_input_persistent)
    return smoluchowski_mmvt_model_input_obj

@pytest.fixture(scope="session")
def smoluchowski_mmvt_model_persistent(tmpdir_factory, 
                                     smoluchowski_mmvt_model_input_persistent):
    """
    Create a model object that is persistent across the tests in this file.
    """
    os.chdir(TEST_DIRECTORY)
    smoluchowski_mmvt_model_obj, model_xml_path \
        = prepare.generate_seekr2_model_and_filetree(
            smoluchowski_mmvt_model_input_persistent, force_overwrite=False)
    model_dir = os.path.dirname(model_xml_path)
    smoluchowski_mmvt_model_obj.anchor_rootdir = os.path.abspath(model_dir)
    # make BD milestones
    smoluchowski_mmvt_model_obj.k_on_info = base.K_on_info()
    bd_milestone = base.BD_milestone()
    bd_milestone.index = 0
    bd_milestone.outer_milestone = smoluchowski_mmvt_model_obj.anchors[-1].milestones[0]
    bd_milestone.inner_milestone = smoluchowski_mmvt_model_obj.anchors[-2].milestones[0]
    smoluchowski_mmvt_model_obj.k_on_info.bd_milestones.append(bd_milestone)
    smoluchowski_mmvt_model_obj.browndye_settings = base.Browndye_settings()
    
    return smoluchowski_mmvt_model_obj

@pytest.fixture
def smoluchowski_mmvt_model(tmpdir_factory, smoluchowski_mmvt_model_persistent):
    """
    Create a copy of the model that is not persistent. But this at least
    doesn't require us to generate an entirely new model
    """
    smoluchowski_mmvt_model = copy.deepcopy(smoluchowski_mmvt_model_persistent)
    return smoluchowski_mmvt_model

@pytest.fixture(scope="session")
def smoluchowski_elber_model_input_persistent(tmpdir_factory):
    """
    Create a model object that is persistent across the tests in this file.
    """
    rootdir = tmpdir_factory.mktemp("smoluchowski_elber")
    smoluchowski_elber_model_input_persistent_obj \
        = create_model_input.create_smoluchowski_elber_model_input(
            rootdir)
    return smoluchowski_elber_model_input_persistent_obj

@pytest.fixture(scope="session")
def smoluchowski_elber_model_persistent(tmpdir_factory, 
                                   smoluchowski_elber_model_input_persistent):
    """
    Create a model object that is persistent across the tests in this file.
    """
    os.chdir(TEST_DIRECTORY)
    #print("elber curdir:", os.getcwd())
    smoluchowski_elber_model_obj, model_xml_path \
        = prepare.generate_seekr2_model_and_filetree(
            smoluchowski_elber_model_input_persistent, force_overwrite=False)
    model_dir = os.path.dirname(model_xml_path)
    smoluchowski_elber_model_obj.anchor_rootdir = os.path.abspath(model_dir)
    smoluchowski_elber_model_obj.k_on_info = base.K_on_info()
    bd_milestone = base.BD_milestone()
    bd_milestone.index = 0
    bd_milestone.outer_milestone = smoluchowski_elber_model_obj.anchors[-1].milestones[1]
    bd_milestone.inner_milestone = smoluchowski_elber_model_obj.anchors[-2].milestones[1]
    smoluchowski_elber_model_obj.k_on_info.bd_milestones.append(bd_milestone)
    smoluchowski_elber_model_obj.browndye_settings = base.Browndye_settings()
    return smoluchowski_elber_model_obj

@pytest.fixture
def smoluchowski_elber_model(tmpdir_factory, smoluchowski_elber_model_persistent):
    """
    Create a copy of the model that is not persistent. But this at least
    doesn't require us to generate an entirely new model
    """
    smoluchowski_elber_model_obj = copy.deepcopy(smoluchowski_elber_model_persistent)
    return smoluchowski_elber_model_obj


def compare_dicts(dict1, dict2):
    """
    Compare the values within two dictionaries and assert they are
    close.
    """
    for key1 in dict1:
        assert key1 in dict2
        assert np.isclose(dict1[key1], dict2[key1])
    return