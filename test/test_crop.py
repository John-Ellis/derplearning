import pytest
import derp.util


@pytest.fixture
def raw_frame():
    return derp.util.load_image("test/100deg.jpg")


def test_patch_bbox_pitch(raw_frame):
    """ verify that the same pixels of all images are cropped as we change pitch """
    frames = [raw_frame[:80], raw_frame[10:90], raw_frame[20:]]
    configs = [{'hfov': 50, 'vfov': 40, 'yaw': 0, 'pitch': 5, 'width': 100, 'height': 80},
               {'hfov': 50, 'vfov': 40, 'yaw': 0, 'pitch': 0, 'width': 100, 'height': 80},
               {'hfov': 50, 'vfov': 40, 'yaw': 0, 'pitch': -5, 'width': 100, 'height': 80}]
    target_config = {'hfov': 10, 'vfov': 10, 'yaw': 0, 'pitch': 0,
                     'width': 100, 'height': 100, 'vcenter': -10, 'hcenter': -10}
    patches = []
    for source_config, frame in zip(configs, frames):
        bbox = derp.util.get_patch_bbox(target_config, source_config)
        patch = derp.util.crop(frame, bbox)
        patches.append(patch)

    for i in range(1, len(patches)):
        prev_patch = patches[i - 1]
        curr_patch = patches[i]
        assert (curr_patch != prev_patch).sum() == 0


def test_patch_bbox_yaw(raw_frame):
    """ verify that the same pixels of all images are cropped as we change yaw """
    frames = [raw_frame[:, :80], raw_frame[:, 10:90], raw_frame[:, 20:]]
    configs = [{'hfov': 40, 'vfov': 50, 'yaw': 5, 'pitch': 0, 'width': 80, 'height': 100},
               {'hfov': 40, 'vfov': 50, 'yaw': 0, 'pitch': 0, 'width': 80, 'height': 100},
               {'hfov': 40, 'vfov': 50, 'yaw': -5, 'pitch': 0, 'width': 80, 'height': 100}]
    target_config = {'hfov': 10, 'vfov': 10, 'yaw': 0, 'pitch': 0,
                     'width': 100, 'height': 100, 'vcenter': -10, 'hcenter': -10}
    patches = []
    for source_config, frame in zip(configs, frames):
        bbox = derp.util.get_patch_bbox(target_config, source_config)
        patch = derp.util.crop(frame, bbox)
        patches.append(patch)

    for i in range(1, len(patches)):
        prev_patch = patches[i - 1]
        curr_patch = patches[i]
        assert (curr_patch != prev_patch).sum() == 0
