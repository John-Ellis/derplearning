import csv
import numpy as np
import os
import PIL.Image
import re
import time
import yaml

def load_image(path):
    """
    Load the RGB version of the image and a PIL image
    """
    with open(path, 'rb') as f:
        with PIL.Image.open(f) as img:
            return img.convert('RGB')                    

def save_image(path, img):
    """
    Store an image numpy array or PIL image to disk
    """
    if type(img) == np.ndarray:
        img = PIL.Image.fromarray((img * 255).astype(np.uint8))
    img.save(path)


def get_name(path):
    """
    The name of a script is it's filename without the extension
    """
    clean_path = path.rstrip('/')
    bn = os.path.basename(clean_path)
    name, ext = os.path.splitext(bn)
    return name


def create_record_folder():
    """
    Generate the name of the record folder and created it
    """
    from datetime import datetime
    import socket
    dt = datetime.utcfromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")
    hn = socket.gethostname()
    path = os.path.join(os.environ['DERP_DATA'], "%s-%s" % (dt, hn))
    print("Creating", path)
    os.mkdir(path)
    return path


def load_config(config_path):
    """ 
    Loads the vehicle config and all requisite components configs
    """

    # Make sure we have a path to a file
    if os.path.isdir(config_path):
        config_path  = os.path.join(config_path, 'config.yaml')
    
    # First load the car's config
    with open(config_path) as f:
        config = yaml.load(f)

    # Make sure we set the name of the config
    if 'name' not in config:
        config['name'] = get_name(config_path)

    # Then load the each component
    dirname = os.path.dirname(config_path)
    for component_config in config['components']:

        # Check if we need to load more parameters from elsewhere
        if 'path' in component_config:
            component_path = os.path.join(dirname, component_config['path'])
            with open(component_path) as f:
                default_component_config = yaml.load(f)

            # Load paramters only if they're not found in default
            for key in default_component_config:
                if key not in component_config:
                    component_config[key] = default_component_config[key]

            # Make sure we have a name for this component
            if 'name' not in component_config:
                component_config['name'] = os.path.basename(os.path.dirname(component_config['path']))

        # Make sure we were able to find a name
        if 'name' not in component_config:
            raise ValueError("load_config: all components must have a name or a path")

        # Make sure we were able to find a class
        if 'class' not in component_config:
            raise ValueError("load_config: all components must have a class in components/")

    # Prepare state from defaults if we have to
    if 'state' not in config:
        config['state'] = {}
    state_defaults = {'offset_speed': 0.0,
                      'offset_steer': 0.0}
    for key in state_defaults:
        if key not in config['state']:
            config['state'][key] = state_defaults[key]

    return config


def load_component(component_config, config):

    # Load the component from its module
    module_name = "derp.components." + component_config['class'].lower()
    class_fn = load_class(module_name, component_config['class'])
    component = class_fn(component_config, config)

    # If we're ready, add it, otherwise make sure it's required
    if not component.ready and component_config['required']:
        raise ValueError("load_components: missing required", component_config['name'])

    print("Loaded component", module_name)
    return component


def load_components(config):
    """
    Load the class of each component by its name and initialize all state keys.
    """
    from derp.state import State
    state = State(config['state'], config)
    components = [state]

    # Initialize components
    for component_config in config['components']:

        # Load the component object
        load_component(component_config, config)

        # if we survived the cull, add the component to 
        components.append(component)

        # Preset all state keys
        if 'state' in component_config:
            for key in component_config['state']:

                # Don't set the key if it's already set and the proposed value is None
                # This allows us to have components request fields, but have a master
                # initializer. Useful for servo or car-specific steer_offset
                val = component_config['state'][key]
                if key not in state or state[key] is None:
                    state[key] = val

    return state, components


def find_component_config(full_config, name, script=None):
    """
    Finds the matching component by name of the component and script if needed
    """
    for component_config in full_config['components']:
        if (component_config['name'] == name
            and (script is None
                 or script == component_config['script'].lower())):
            return component_config
    

def load_class(path, name):
    """ 
    Loads the class "name" at relative path (period separated) "path" and returns it
    """
    from importlib import import_module
    m = import_module(path)
    c = getattr(m, name)
    return c


def read_csv(path, floats=True):
    """
    Read through the state file and get our timestamps and recorded values.
    Returns the non-timestamp headers, timestamps as 
    """
    timestamps = []
    states = []
    with open(path) as f:
        reader = csv.reader(f)
        headers = next(reader)[1:]
        for line in reader:
            if not len(line):
                continue
            state = []
            timestamps.append(int(re.sub('\D', '', line[0] ) ) )
            #regex to remove any non-decimal characters from the timestamp so that 
            #it can be read as an int
            for value in line[1:]:
                value = float(value) if floats else value
                state.append(value)
            states.append(state)
    timestamps = np.array(timestamps, dtype=np.uint64)
    if floats:
        states = np.array(states, dtype=np.float)
    return timestamps, headers, states


def find_value(haystack, key, values, interpolate=False):
    """
    Find the nearest value in the sorted haystack to the specified key.
    """

    nearest = 0
    diff = np.abs(haystack - key)
    if interpolate:
        nearest = diff.argsort()[:2]
        return (values[nearest[0]] + values[nearest[1]]) / 2

    nearest = diff.argmin()
    return values[nearest]


def find_matching_file(path, name_pattern):
    """
    Finds a file that matches the given name regex
    """
    pattern = re.compile(name_pattern)
    for filename in os.listdir(path):
        if pattern.search(filename) is not None:
            return os.path.join(path, filename)
    return None
