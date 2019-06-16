import hashlib
import sys
import os
# There's some issue with Nvidia OpenGL. Render works fine on the mesa one.
os.environ['MUJOCO_GL'] = 'osmesa'

import gym
import numpy as np
from dm_control import suite
from dm_control.rl import specs
from gym import core, spaces
from gym.utils import seeding
from gym.envs.registration import registry


class Discrete(gym.spaces.Discrete):
    # Wrapper for discrete action space in dm_control
    def __init__(self, _minimum, _maximum):
        super().__init__(_maximum - _minimum)
        self.offset = _minimum  # offset is used when send action to real env


def convert_action_space(spec, clip_inf=False):
    # action space used in dm_control is Spec object
    if spec.dtype == np.int:  # Discrete
        return Discrete(spec.minimum, spec.maximum)
    else:  # Box
        if type(spec) is specs.ArraySpec:
            return spaces.Box(-np.inf, np.inf, shape=spec.shape)
        elif type(spec) is specs.BoundedArraySpec:
            _min = spec.minimum
            _max = spec.maximum
            max_float = sys.float_info.max

            if clip_inf:
                _min = np.clip(spec.minimum, -max_float, max_float)
                _max = np.clip(spec.maximum, -max_float, max_float)

            if np.isscalar(_min) and np.isscalar(_max):
                # same min and max for every element
                return spaces.Box(_min, _max, shape=spec.shape)
            else:
                # different min and max for every element
                return spaces.Box(_min + np.zeros(spec.shape),
                                  _max + np.zeros(spec.shape))
        else:
            raise ValueError('Unknown spec type {}'.format(type(spec)))


def convert_observation_space(odict):
    # observation space used in dm_control is OrderedDict object
    if len(odict.keys()) == 1:
        # no concatenation
        return convert_action_space(next(odict.values()), False)
    else:
        # concatenation
        n = sum([np.int(np.prod(odict[key].shape)) for key in odict])
        return spaces.Box(-np.inf, np.inf, shape=(n, ))


def convert_observation(spec_obs):
    if len(spec_obs.keys()) == 1:
        # no concatenation
        return next(spec_obs.values())
    else:
        # concatenation
        n = sum([np.int(np.prod(spec_obs[key].shape)) for key in spec_obs])
        space_obs = np.zeros((n, ))
        i = 0
        for key in spec_obs:
            space_obs[i:i+np.prod(spec_obs[key].shape)] = spec_obs[key].ravel()
            i += np.prod(spec_obs[key].shape)
        return space_obs


class Env(core.Env):
    def __init__(self, domain_name, task_name, *args, **kwargs):

        self.dmc_env = suite.load(
            domain_name=domain_name, task_name=task_name, *args, **kwargs)

        # convert spec to space
        self.action_space = \
            convert_action_space(self.dmc_env.action_spec(), True)
        self.observation_space = \
            convert_observation_space(self.dmc_env.observation_spec())

        self.time_step = None
        self.viewer = None
        self.seed()

    def get_observation(self):
        return convert_observation(self.time_step.observation)

    def seed(self, seed=None):
        rng, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.time_step = self.dmc_env.reset()
        return self.get_observation()

    def step(self, a):
        if type(self.action_space) == Discrete:
            a += self.action_space.offset
        self.time_step = self.dmc_env.step(a)

        return (
            self.get_observation(),
            self.time_step.reward,
            self.time_step.last(),
            {}
        )

    def render(self, mode='human', camera_ids=None, w=120, h=160):
        """
        Args:
            mode (str): consistent with AtariEnv in Gym. Mode human will display
                        images on the window, where views from different cameras
                        are in one row.
            camera_ids (list[int]): camera id list, detail meaning can be found
                                    in dm_control
            w (int): render screen width of each camera
            h (int): render screen height of each camera
        """
        if camera_ids is None:
            camera_ids = [0]
        img = np.concatenate([self.dmc_env.physics.render(w, h, camera_id)
                              for camera_id in camera_ids], 1)

        if mode == 'rgb_array':
            return img
        elif mode == 'human':
            from gym.envs.classic_control import rendering
            if self.viewer is None:
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(img)
            return self.viewer.isopen

    def close(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None


def make(domain_name, task_name, task_kwargs=None, visualize_reward=False):
    # register environment
    prehash_id = domain_name + task_name + str(visualize_reward)
    if task_kwargs is not None:
        prehash_id += str(sorted(task_kwargs.items()))
    h = hashlib.md5(prehash_id.encode())
    gym_id = h.hexdigest() + '-v0'

    # avoid re-registering
    if gym_id not in registry.env_specs:
        registry.register(
            id=gym_id,
            entry_point='dm2gym:Env',
            kwargs={'domain_name': domain_name,
                    'task_name': task_name,
                    'task_kwargs': task_kwargs,
                    'visualize_reward': visualize_reward}
        )

    # make the Open AI env
    return gym.make(gym_id)
