# dm_control_gym_wrapper
OpenAI Gym Wrapper for the DeepMind Control Suite


Note that there's some issue on Nvidia OpenGL. Rendering backend is specified to the OSMesa, which 
can be modified on the head of `dm2gym.py`. 


`RuntimeError` will be raised after the program has been terminated, which is by design. 
See [issue in dm_control](https://github.com/deepmind/dm_control/issues/79) for details.


Different apis with OpenAI Gym are list as follows:
1. `make` is consistent with `suite.load` in `dm_control`.
2. `env.render` has four parameters where one can specific cameras or mode. More details can be found in codes.


Except the api of `make` and `env.render` whose document can be found in definition codes, others are same as gym.

Simple usages:
```python
import dm2gym


env = dm2gym.make(domain_name="cartpole", task_name="balance")
env.reset()
for t in range(1000):
    env.render('human', camera_ids=[0, 1])
    a = env.action_space.sample()
    observation, reward, done, info = env.step(a)
    if done:
        env.reset()

```