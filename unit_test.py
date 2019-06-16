import dm2gym


env = dm2gym.make(domain_name="cartpole", task_name="balance")
env.reset()
for t in range(1000):
    env.render('human', camera_ids=[0, 1])
    a = env.action_space.sample()
    observation, reward, done, info = env.step(a)
    if done:
        env.reset()
