# -*- coding: utf-8 -*-
"""
Functions to integrate your model with the DEEPaaS API.
It's usually good practice to keep this file minimal, only performing
the interfacing tasks. In this way you don't mix your true code with
DEEPaaS code and everything is more modular. That is, if you need to write
the predict() function in api.py, you would import your true predict function
and call it from here (with some processing / postprocessing in between
if needed).
For example:

    import mycustomfile

    def predict(**kwargs):
        args = preprocess(kwargs)
        resp = mycustomfile.predict(args)
        resp = postprocess(resp)
        return resp

To start populating this file, take a look at the docs [1] and at
an exemplar module [2].

[1]: https://docs.ai4os.eu/
[2]: https://github.com/ai4os-hub/ai4os-demo-app
"""

import ast
import base64
import json
import math
import mimetypes
from pathlib import Path
import pkg_resources
from random import random
import shutil
import tempfile
import time

from deepaas.model.v2.wrapper import UploadedFile
from tensorboardX import SummaryWriter
from webargs import fields, validate

from ai4os_demo_app.misc import launch_tensorboard

# from ai4os_demo_app.misc import _catch_error


BASE_DIR = Path(__file__).resolve().parents[1]


# TODO: reenable catch error when this issue is fixed
# https://github.com/ai4os/DEEPaaS/issues/174
# @_catch_error
def get_metadata():
    """
    DO NOT REMOVE - All modules should have a get_metadata() function
    with appropriate keys.
    """
    distros = list(pkg_resources.find_distributions(str(BASE_DIR), only=True))
    if len(distros) == 0:
        raise Exception("No package found.")
    pkg = distros[0]  # if several select first

    meta_fields = {
        "name": None,
        "author": None,
        "author-email": None,
        "description": None,
        "license": None,
        "version": None,
    }
    meta = {}
    for line in pkg.get_metadata_lines("PKG-INFO"):
        line_low = line.lower()  # to avoid inconsistency due to letter cases
        for k in meta_fields:
            if line_low.startswith(k + ":"):
                _, value = line.split(": ", 1)
                meta[k] = value

    return meta


def get_train_args():
    arg_dict = {
        "epoch_num": fields.Int(
            required=False,
            missing=10,
            description="Total number of training epochs",
        ),
    }
    return arg_dict


def train(**kwargs):
    """
    Dummy training. We just sleep for some number of epochs
    (1 epoch = 1 second)
    mimicking some computation taking place.
    We log some random metrics in Tensorboard to mimic monitoring.
    """
    logdir = BASE_DIR / "models" / time.strftime("%Y-%m-%d_%H-%M-%S")
    writer = SummaryWriter(logdir=logdir, flush_secs=1)
    launch_tensorboard(logdir=logdir)
    for epoch in range(kwargs["epoch_num"]):
        time.sleep(1.0)
        writer.add_scalar(  # fake loss with random noise
            "scalars/loss", -math.log(epoch + 1) * (1 + random() * 0.2), epoch  # nosec
        )
        writer.add_scalar(  # fake accuracy with random noise (clipped to 1)
            "scalars/accuracy",
            min((1 - 1 / (epoch + 1)) * (1 + random() * 0.1), 1),  # nosec
            epoch,
        )
    writer.close()

    # Write a fake model file
    (logdir / "final_model.hdf5").touch()

    return {"status": "done", "final accuracy": 0.9}


def get_predict_args():
    """
    TODO: add more dtypes
    * int with choices
    * composed: list of strs, list of int
    """
    # WARNING: missing!=None has to go with required=False
    # fmt: off
    arg_dict = {
        "demo_str": fields.Str(
            required=False,
            missing="some-string",
            description="test string",
        ),
        "demo_str_choice": fields.Str(
            required=False,
            missing="choice2",
            enum=["choice1", "choice2"],
            description="test multi-choice with strings",
        ),
        "demo_int": fields.Int(
            required=False,
            missing=1,
            description="test integer",
        ),
        "demo_int_range": fields.Int(
            required=False,
            missing=50,
            validate=[validate.Range(min=1, max=100)],
            description="test integer is inside a min-max range",
        ),
        "demo_float": fields.Float(
            required=False,
            missing=0.1,
            description="test float",
        ),
        "demo_bool": fields.Bool(
            required=False,
            missing=True,
            description="test boolean",
        ),
        "demo_dict": fields.Str(
            # dicts have to be processed as strings otherwise DEEPaaS Swagger UI
            # throws an error
            required=False,
            missing="{'a': 0, 'b': 1}",
            description="test dictionary",
        ),
        "demo_list_of_floats": fields.List(
            fields.Float(),
            required=False,
            missing=[0.1, 0.2, 0.3],
            description="test list of floats",
        ),
        "demo_image": fields.Field(
            required=True,
            type="file",
            location="form",
            description="test image upload",  # "image" word in description is needed to be parsed by Gradio UI
        ),
        "demo_audio": fields.Field(
            required=True,
            type="file",
            location="form",
            description="test audio upload",  # "audio" word in description is needed to be parsed by Gradio UI
        ),
        "demo_video": fields.Field(
            required=True,
            type="file",
            location="form",
            description="test video upload",  # "video" word in description is needed to be parsed by Gradio UI
        ),
        # Add format type of the response of predict()
        # For demo purposes, we allow the user to receive back either JSON, image or zip.
        # More options for MIME types: https://mimeapplication.net/
        "accept": fields.Str(
            required=False,
            missing="application/json",
            description="Format of the response.",
            validate=validate.OneOf(["application/json", "application/zip", "image/*"]),
        ),
    }
    # fmt: on
    return arg_dict


# @_catch_error
def predict(**kwargs):
    """
    Return same inputs as provided. We also add additional fields
    to test the functionality of the Gradio-based UI [1].
    [1]: https://github.com/ai4os/deepaas_ui
    """
    # Dict are fed as str so have to be converted back
    kwargs["demo_dict"] = ast.literal_eval(kwargs["demo_dict"])

    # Check that the main input types are received in the correct Python type
    arg2type = {
        "demo_str": str,
        "demo_int": int,
        "demo_float": float,
        "demo_bool": bool,
        "demo_dict": dict,
        "demo_image": UploadedFile,
    }

    for k, v in arg2type.items():
        if not isinstance(kwargs[k], v):
            message = (
                f"Key {k} is type {type(kwargs[k])}, not type {v}. \n"
                f"Value: {kwargs[k]}"
            )
            raise Exception(message)

    # Add labels and random probabilities to output as mock
    prob = [random() for _ in range(5)]  # nosec
    kwargs["probabilities"] = [i / sum(prob) for i in prob]
    kwargs["labels"] = ["class2", "class3", "class0", "class1", "class4"]

    # Format the response differently depending on the MIME type selected by the user
    if kwargs["accept"] == "application/json":
        # Read media files and return them back in base64
        for k in ["demo_image", "demo_audio", "demo_video"]:
            with open(kwargs[k].filename, "rb") as f:
                media = f.read()
            media = base64.b64encode(media)  # bytes
            kwargs[k] = media.decode("utf-8")  # string (in utf-8)

        return kwargs

    elif kwargs["accept"] == "application/zip":
        zip_dir = tempfile.TemporaryDirectory()
        zip_dir = Path(zip_dir.name)
        zip_dir.mkdir()

        # Save parameters to JSON file
        with open(zip_dir / "args.json", "w") as f:
            json.dump(kwargs, f, sort_keys=True, indent=4)

        # Copy media files to ZIP folder
        for k in ["demo_image", "demo_audio", "demo_video"]:
            # Try to guess extension, otherwise take last part of content type
            ext = mimetypes.guess_extension(kwargs[k].content_type)
            extension = ext if ext else f".{kwargs[k].content_type.split('/')[-1]}"

            shutil.copyfile(src=kwargs[k].filename, dst=zip_dir / f"{k}{extension}")

        # Pack folder into ZIP file and return it
        shutil.make_archive(zip_dir, format="zip", root_dir=zip_dir)

        return open(f"{zip_dir}.zip", "rb")

    elif kwargs["accept"] == "image/*":
        filepath = kwargs["demo_image"].filename

        return open(filepath, "rb")


# Schema to validate the `predict()` output if accept field is "application/json"
schema = {
    "demo_str": fields.Str(),
    "demo_str_choice": fields.Str(),
    "demo_int": fields.Int(),
    "demo_int_range": fields.Int(),
    "demo_float": fields.Float(),
    "demo_bool": fields.Bool(),
    "demo_dict": fields.Dict(),
    "demo_list_of_floats": fields.List(fields.Float()),
    "demo_image": fields.Str(
        description="image"  # description needed to be parsed by UI
    ),
    "demo_audio": fields.Str(
        description="audio"  # description needed to be parsed by UI
    ),
    "demo_video": fields.Str(
        description="video"  # description needed to be parsed by UI
    ),
    "labels": fields.List(fields.Str()),
    "probabilities": fields.List(fields.Float()),
    "accept": fields.Str(),
}
