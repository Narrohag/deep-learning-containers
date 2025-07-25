import os
import sys
import logging

import pytest
from packaging.version import Version
from packaging.specifiers import SpecifierSet

import test.test_utils.ec2 as ec2_utils
from test import test_utils
from test.test_utils import (
    CONTAINER_TESTS_PREFIX,
    get_framework_and_version_from_tag,
    get_inference_server_type,
    login_to_ecr_registry,
    get_account_id_from_image_uri,
)
from test.test_utils.ec2 import (
    get_ec2_instance_type,
    execute_ec2_inference_test,
    get_ec2_accelerator_type,
    execute_ec2_telemetry_test,
)
from test.dlc_tests.conftest import LOGGER

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.INFO)


PT_EC2_GPU_INSTANCE_TYPE = get_ec2_instance_type(default="g4dn.8xlarge", processor="gpu")
PT_EC2_CPU_INSTANCE_TYPE = get_ec2_instance_type(default="c5.9xlarge", processor="cpu")
PT_EC2_GPU_EIA_INSTANCE_TYPE = get_ec2_instance_type(
    default="g4dn.8xlarge",
    processor="gpu",
    filter_function=ec2_utils.filter_not_heavy_instance_types,
)
PT_EC2_EIA_ACCELERATOR_TYPE = get_ec2_accelerator_type(default="eia1.large", processor="eia")
PT_EC2_NEURON_INSTANCE_TYPE = get_ec2_instance_type(default="inf1.xlarge", processor="neuron")
PT_EC2_SINGLE_GPU_INSTANCE_TYPE = get_ec2_instance_type(
    default="g5.8xlarge",
    processor="gpu",
    filter_function=ec2_utils.filter_only_single_gpu,
)

PT_EC2_CPU_GRAVITON_INSTANCE_TYPE = get_ec2_instance_type(
    default="c6g.8xlarge", processor="cpu", arch_type="graviton"
)
PT_EC2_GPU_GRAVITON_INSTANCE_TYPE = get_ec2_instance_type(
    default="g5g.4xlarge", processor="gpu", arch_type="graviton"
)
PT_EC2_CPU_ARM64_INSTANCE_TYPE = get_ec2_instance_type(
    default="c6g.8xlarge", processor="cpu", arch_type="arm64"
)
PT_EC2_GPU_ARM64_INSTANCE_TYPE = get_ec2_instance_type(
    default="g5g.4xlarge", processor="gpu", arch_type="arm64"
)

PT_EC2_NEURON_TRN1_INSTANCE_TYPE = get_ec2_instance_type(
    default="trn1.2xlarge", processor="neuronx", job_type="inference"
)
PT_EC2_NEURON_INF2_INSTANCE_TYPE = get_ec2_instance_type(
    default="inf2.xlarge", processor="neuronx", job_type="inference"
)

PT_TELEMETRY_CMD = os.path.join(CONTAINER_TESTS_PREFIX, "testTelemetry")
PT_TORCHAUDIO_CMD = os.path.join(CONTAINER_TESTS_PREFIX, "pytorch_tests", "testTorchaudio")
PT_TORCHDATA_CMD = os.path.join(CONTAINER_TESTS_PREFIX, "pytorch_tests", "testTorchdata")
PT_TORCHDATA_DEV_CMD = os.path.join(CONTAINER_TESTS_PREFIX, "pytorch_tests", "testTorchdataDev")


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.skipif(
    not test_utils.is_deep_canary_context() or not os.getenv("REGION") == "us-west-2",
    reason="This test only needs to run in deep-canary context in us-west-2",
)
@pytest.mark.deep_canary("Reason: This test is a simple pytorch inference test")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_ec2_pytorch_inference_gpu_deep_canary(
    pytorch_inference, ec2_connection, region, gpu_only, ec2_instance_type
):
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    ec2_pytorch_inference(pytorch_inference, "gpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.skipif(
    not test_utils.is_deep_canary_context() or not os.getenv("REGION") == "us-west-2",
    reason="This test only needs to run in deep-canary context in us-west-2",
)
@pytest.mark.deep_canary("Reason: This test is a simple pytorch inference test")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_ec2_pytorch_inference_cpu_deep_canary(pytorch_inference, ec2_connection, region, cpu_only):
    ec2_pytorch_inference(pytorch_inference, "cpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.skipif(
    not test_utils.is_deep_canary_context() or not os.getenv("REGION") == "us-west-2",
    reason="This test only needs to run in deep-canary context in us-west-2",
)
@pytest.mark.deep_canary("Reason: This test is a simple pytorch inference test")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_GRAVITON_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_graviton_gpu_deep_canary(
    pytorch_inference_graviton, ec2_connection, region, gpu_only
):
    ec2_pytorch_inference(pytorch_inference_graviton, "gpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.skipif(
    not test_utils.is_deep_canary_context() or not os.getenv("REGION") == "us-west-2",
    reason="This test only needs to run in deep-canary context in us-west-2",
)
@pytest.mark.deep_canary("Reason: This test is a simple pytorch inference test")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_arm64_gpu_deep_canary(
    pytorch_inference_arm64, ec2_connection, region, gpu_only
):
    ec2_pytorch_inference(pytorch_inference_arm64, "gpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.skipif(
    not test_utils.is_deep_canary_context() or not os.getenv("REGION") == "us-west-2",
    reason="This test only needs to run in deep-canary context in us-west-2",
)
@pytest.mark.deep_canary("Reason: This test is a simple pytorch inference test")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_GRAVITON_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_graviton_cpu_deep_canary(
    pytorch_inference_graviton, ec2_connection, region, cpu_only
):
    ec2_pytorch_inference(pytorch_inference_graviton, "cpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.skipif(
    not test_utils.is_deep_canary_context() or not os.getenv("REGION") == "us-west-2",
    reason="This test only needs to run in deep-canary context in us-west-2",
)
@pytest.mark.deep_canary("Reason: This test is a simple pytorch inference test")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_arm64_cpu_deep_canary(
    pytorch_inference_arm64, ec2_connection, region, cpu_only
):
    ec2_pytorch_inference(pytorch_inference_arm64, "cpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.model("resnet")
@pytest.mark.parametrize("ec2_instance_ami", [test_utils.NEURON_INF1_AMI_US_WEST_2], indirect=True)
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_NEURON_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("neuron")
def test_ec2_pytorch_inference_neuron(pytorch_inference_neuron, ec2_connection, region):
    ec2_pytorch_inference(pytorch_inference_neuron, "neuron", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.model("resnet")
@pytest.mark.parametrize("ec2_instance_ami", [test_utils.UL22_BASE_NEURON_US_WEST_2], indirect=True)
@pytest.mark.team("neuron")
@pytest.mark.parametrize(
    "ec2_instance_type",
    PT_EC2_NEURON_TRN1_INSTANCE_TYPE + PT_EC2_NEURON_INF2_INSTANCE_TYPE,
    indirect=True,
)
def test_ec2_pytorch_inference_neuronx(pytorch_inference_neuronx, ec2_connection, region):
    ec2_pytorch_inference(pytorch_inference_neuronx, "neuronx", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker", "stabilityai")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_ec2_pytorch_inference_gpu(
    pytorch_inference, ec2_connection, region, gpu_only, ec2_instance_type
):
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    ec2_pytorch_inference(pytorch_inference, "gpu", ec2_connection, region)


@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_ec2_pytorch_inference_cpu(pytorch_inference, ec2_connection, region, cpu_only):
    ec2_pytorch_inference(pytorch_inference, "cpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_GRAVITON_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_graviton_cpu(
    pytorch_inference_graviton, ec2_connection, region, cpu_only
):
    ec2_pytorch_inference(pytorch_inference_graviton, "cpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_arm64_cpu(pytorch_inference_arm64, ec2_connection, region, cpu_only):
    ec2_pytorch_inference(pytorch_inference_arm64, "cpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_GRAVITON_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_graviton_gpu(
    pytorch_inference_graviton, ec2_connection, region, gpu_only
):
    ec2_pytorch_inference(pytorch_inference_graviton, "gpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.model("densenet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_ec2_pytorch_inference_arm64_gpu(pytorch_inference_arm64, ec2_connection, region, gpu_only):
    ec2_pytorch_inference(pytorch_inference_arm64, "gpu", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("elastic_inference")
@pytest.mark.model("resnet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize("ei_accelerator_type", PT_EC2_EIA_ACCELERATOR_TYPE, indirect=True)
def test_ec2_pytorch_inference_eia_cpu(
    pytorch_inference_eia, ec2_connection, region, pt14_and_above_only
):
    ec2_pytorch_inference(pytorch_inference_eia, "eia", ec2_connection, region)


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("elastic_inference")
@pytest.mark.model("resnet")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_EIA_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize("ei_accelerator_type", PT_EC2_EIA_ACCELERATOR_TYPE, indirect=True)
def test_ec2_pytorch_inference_eia_gpu(
    pytorch_inference_eia, ec2_connection, region, pt14_and_above_only
):
    ec2_pytorch_inference(pytorch_inference_eia, "eia", ec2_connection, region)


@pytest.mark.usefixtures("feature_torchaudio_present")
@pytest.mark.usefixtures("sagemaker", "stabilityai")
@pytest.mark.integration("pt_torchaudio_gpu")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_torchaudio_gpu(
    pytorch_inference, ec2_connection, gpu_only, ec2_instance_type
):
    _, image_framework_version = get_framework_and_version_from_tag(pytorch_inference)
    if Version(image_framework_version) not in SpecifierSet("!=1.9.*,!=1.10.*"):
        pytest.skip("torchaudio is not supported in PT 1.9 and 1.10")
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    execute_ec2_inference_test(ec2_connection, pytorch_inference, PT_TORCHAUDIO_CMD)


@pytest.mark.usefixtures("feature_torchaudio_present")
@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("pt_torchaudio_cpu")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_torchaudio_cpu(pytorch_inference, ec2_connection, cpu_only):
    _, image_framework_version = get_framework_and_version_from_tag(pytorch_inference)
    if Version(image_framework_version) not in SpecifierSet("!=1.9.*,!=1.10.*"):
        pytest.skip("torchaudio is not supported in PT 1.9 and 1.10")
    execute_ec2_inference_test(ec2_connection, pytorch_inference, PT_TORCHAUDIO_CMD)


@pytest.mark.skip_torchdata_test
@pytest.mark.usefixtures("feature_torchdata_present")
@pytest.mark.usefixtures("sagemaker", "stabilityai")
@pytest.mark.integration("pt_torchdata_gpu")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_torchdata_gpu(
    pytorch_inference, ec2_connection, gpu_only, ec2_instance_type, pt111_and_above_only
):
    _, image_framework_version = get_framework_and_version_from_tag(pytorch_inference)
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    if Version(image_framework_version) in SpecifierSet(">=1.11,<1.14"):
        execute_ec2_inference_test(ec2_connection, pytorch_inference, PT_TORCHDATA_DEV_CMD)
    else:
        execute_ec2_inference_test(ec2_connection, pytorch_inference, PT_TORCHDATA_CMD)


@pytest.mark.skip_torchdata_test
@pytest.mark.usefixtures("feature_torchdata_present")
@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("pt_torchdata_cpu")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_torchdata_cpu(
    pytorch_inference, ec2_connection, cpu_only, pt111_and_above_only
):
    _, image_framework_version = get_framework_and_version_from_tag(pytorch_inference)
    if Version(image_framework_version) in SpecifierSet(">=1.11,<1.14"):
        execute_ec2_inference_test(ec2_connection, pytorch_inference, PT_TORCHDATA_DEV_CMD)
    else:
        execute_ec2_inference_test(ec2_connection, pytorch_inference, PT_TORCHDATA_CMD)


def ec2_pytorch_inference(image_uri, processor, ec2_connection, region):
    repo_name, image_tag = image_uri.split("/")[-1].split(":")
    container_name = f"{repo_name}-{image_tag}-ec2"
    model_name = "pytorch-densenet"
    if processor == "eia":
        image_framework, image_framework_version = get_framework_and_version_from_tag(image_uri)
        if image_framework_version == "1.3.1":
            model_name = "pytorch-densenet-v1-3-1"
    if processor == "neuron":
        model_name = "pytorch-resnet-neuron"
    if processor == "neuronx":
        model_name = "pytorch-resnet-neuronx"
    processor_is_neuron = "neuron" in processor

    inference_cmd = test_utils.get_inference_run_command(image_uri, model_name, processor)
    docker_runtime = "--runtime=nvidia --gpus all" if "gpu" in image_uri else ""
    docker_init = " --init" if test_utils.is_ec2_image(image_uri) else ""

    if processor_is_neuron:
        docker_run_cmd = (
            f"docker run {docker_runtime} -itd --name {container_name}"
            f" -p 80:8080 -p 8081:8081"
            f" --device=/dev/neuron0 --cap-add IPC_LOCK"
            f" --env NEURON_MONITOR_CW_REGION={region}"
            f" {image_uri} {inference_cmd}"
        )
    else:
        docker_run_cmd = (
            f"docker run {docker_runtime} -itd{docker_init} --name {container_name}"
            f" -p 80:8080 -p 8081:8081"
            f" {image_uri} {inference_cmd}"
        )
    try:
        account_id = get_account_id_from_image_uri(image_uri)
        login_to_ecr_registry(ec2_connection, account_id, region)
        LOGGER.info(docker_run_cmd)
        ec2_connection.run(docker_run_cmd, hide=True)
        server_type = get_inference_server_type(image_uri)
        inference_result = test_utils.request_pytorch_inference_densenet(
            connection=ec2_connection, model_name=model_name, server_type=server_type
        )
        assert (
            inference_result
        ), f"Failed to perform pytorch inference test for image: {image_uri} on ec2"

    finally:
        ec2_connection.run(f"docker rm -f {container_name}", warn=True, hide=True)


@pytest.mark.usefixtures("sagemaker", "stabilityai")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_SINGLE_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_telemetry_entrypoint_gpu(
    pytorch_inference, ec2_connection, gpu_only, ec2_instance_type, pt15_and_above_only
):
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker", "stabilityai")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_SINGLE_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_telemetry_bashrc_gpu(
    pytorch_inference, ec2_connection, gpu_only, ec2_instance_type, pt15_and_above_only
):
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker", "stabilityai")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_SINGLE_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_telemetry_framework_gpu(
    pytorch_inference, ec2_connection, gpu_only, ec2_instance_type, pt15_and_above_only
):
    if test_utils.is_image_incompatible_with_instance_type(pytorch_inference, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_inference} is incompatible with instance type {ec2_instance_type}"
        )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "framework",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_telemetry_entrypoint_cpu(
    pytorch_inference, ec2_connection, cpu_only, pt15_and_above_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_telemetry_bashrc_cpu(
    pytorch_inference, ec2_connection, cpu_only, pt15_and_above_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.team("conda")
def test_pytorch_inference_telemetry_framework_cpu(
    pytorch_inference, ec2_connection, cpu_only, pt15_and_above_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference,
        "framework",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_GRAVITON_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_framework_graviton_cpu(
    pytorch_inference_graviton, ec2_connection, cpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_graviton,
        "framework",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_framework_arm64_cpu(
    pytorch_inference_arm64, ec2_connection, cpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "framework",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_entrypoint_arm64_cpu(
    pytorch_inference_arm64, ec2_connection, cpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_CPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_bashrc_arm64_cpu(
    pytorch_inference_arm64, ec2_connection, cpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_GRAVITON_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_framework_graviton_gpu(
    pytorch_inference_graviton, ec2_connection, gpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_graviton,
        "framework",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_framework_arm64_gpu(
    pytorch_inference_arm64, ec2_connection, gpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "framework",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_entrypoint_arm64_gpu(
    pytorch_inference_arm64, ec2_connection, gpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "entrypoint",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("telemetry")
@pytest.mark.model("N/A")
@pytest.mark.parametrize("ec2_instance_type", PT_EC2_GPU_ARM64_INSTANCE_TYPE, indirect=True)
@pytest.mark.parametrize(
    "ec2_instance_ami", [test_utils.AL2023_BASE_DLAMI_ARM64_US_WEST_2], indirect=True
)
def test_pytorch_inference_telemetry_bashrc_arm64_gpu(
    pytorch_inference_arm64, ec2_connection, gpu_only
):
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=False,
    )
    execute_ec2_telemetry_test(
        ec2_connection,
        pytorch_inference_arm64,
        "bashrc",
        "pytorch_inf_telemetry",
        test_cmd=PT_TELEMETRY_CMD,
        opt_in=True,
    )
