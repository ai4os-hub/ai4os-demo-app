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

import math
from pathlib import Path
import pkg_resources
from random import random
import shutil
import tempfile
import time

from tensorboardX import SummaryWriter
from webargs import fields, validate


from ai4os_demo_app.misc import _catch_error, launch_tensorboard


BASE_DIR = Path(__file__).resolve().parents[1]


@_catch_error
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
        "version": None,
        "summary": None,
        "home-page": None,
        "author": None,
        "author-email": None,
        "license": None,
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
    Dummy training. We just sleep for some number of epochs (1 epoch = 1 second)
    mimicking some computation taking place.
    We log some random metrics in Tensorboard to mimic monitoring.
    """
    logdir = BASE_DIR / "models" / time.strftime("%Y-%m-%d_%H-%M-%S")
    writer = SummaryWriter(logdir=logdir, flush_secs=1)
    launch_tensorboard(logdir=logdir)
    for epoch in range(kwargs["epoch_num"]):
        time.sleep(1.)
        writer.add_scalar(  # fake loss with random noise
            "scalars/loss",
            - math.log(epoch + 1) * (1 + random() * 0.2),
            epoch)
        writer.add_scalar(  # fake accuracy with random noise (clipped to 1)
            "scalars/accuracy",
            min((1 - 1/ (epoch+1)) * (1 + random() * 0.1), 1),
            epoch)
    writer.close()

    # Write a fake model file
    (logdir / 'final_model.hdf5').touch()

    return {"status": "done", "final accuracy": 0.9}


def get_predict_args():
    """
    Input fields for the user.
    """
    arg_dict = {
        "demo-image": fields.Field(
            required=True,
            type="file",
            location="form",
            description="image",  # needed to be parsed by UI
        ),
        # Add format type of the response of predict()
        # For demo purposes, we allow the user to receive back
        # either an image or a zip containing an image.
        # More options for MIME types: https://mimeapplication.net/
        "accept": fields.Str(
            description="Media type(s) acceptable for the response.",
            validate=validate.OneOf(["image/*", "application/zip"]),
        ),
    }
    return arg_dict


@_catch_error
def predict(**kwargs):
    """
    Return same inputs as provided.
    """
    filepath = kwargs['demo-image'].filename

    # Return the image directly
    if kwargs['accept'] == 'image/*':
        return open(filepath, 'rb')

    # Return a zip
    elif kwargs['accept'] == 'application/zip':

        zip_dir = tempfile.TemporaryDirectory()

        # Add original image to output zip
        shutil.copyfile(filepath,
                        zip_dir.name + '/demo.png')

        # Add for example a demo txt file
        with open(f'{zip_dir.name}/demo.txt', 'w') as f:
            f.write('Add here any additional information!')

        # Pack dir into zip and return it
        shutil.make_archive(
            zip_dir.name,
            format='zip',
            root_dir=zip_dir.name,
        )
        zip_path = zip_dir.name + '.zip'

        return open(zip_path, 'rb')
