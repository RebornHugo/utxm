import os
import pickle
os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle,dill'
os.environ['PYRO_SERIALIZER'] = 'pickle'

from baselines.common.vec_env.subproc_vec_env import SubprocVecEnv
from run_common import make_env
import Pyro4.naming
from multiprocessing import cpu_count
from PyQt5 import QtCore, QtGui
import gym
import gym.monitoring

#app = QtGui.QGuiApplication([])


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class EnvServerMulti(object):
    def __init__(self):
        self.envs = {}
        self.videos = {}

    def make_env(self, env_id, seed, id=None, num_processes=None):

        if id in self.envs:
            '''
            if force_new or env_id != self.env_id or self.num_envs != num_processes:
                self.close()
            else:
                print('env existed, use created env')
                return True
            '''
            #self.close(id)
            pass
        if num_processes is None:
            num_processes = cpu_count()

        if num_processes == 0:
            self.envs[id] = make_env(env_id, seed, rank=0, log_dir=None, visualize=False)()

        else:
            self.envs[id] = SubprocVecEnv([
                make_env(env_id, seed, rank=i, log_dir=None, visualize=False)
                for i in range(num_processes)
            ])
        print( 'Started! env_id:{}, seed:{}, num_processes:{}, id:{}'.format( env_id, seed, num_processes, id ) )
        return True

    def step(self, actions, id=None):
        return self.envs[id].step(actions)

    def reset(self, id=None, *args,**kwargs):
        return self.envs[id].reset(*args, **kwargs)


    def close(self, id=None):
        self.envs[id].close()
        del self.envs[id]
        print('Stoped! id:{}'.format( id ))
        return True

    def start_video(self, filename, id=None):
        self.videos[id] = gym.monitoring.video_recorder.VideoRecorder(env=self.envs[id], base_path=(filename),
                                                                      enabled=True)

    def render_video(self, id=None):
        self.videos[id].capture_frame()
        return True

    def close_video(self, id=None):
        self.videos[id].close()
        print('close video{}'.format(id))

        return True

    def render(self, id=None, *arg):
        return self.envs[id].render(*arg)

    def debug(self, id=None):
        return True

    def action_space(self, id=None):
        return self.envs[id].action_space

    def observation_space(self, id=None):
        return self.envs[id].observation_space

    def num_envs(self, id=None):
        return self.envs[id].num_envs

    def num_cpus(self, id=None):
        return cpu_count()





if __name__ == '__main__':
    def te():
        env = EnvServerMulti()
        env.make_env(env_id='Pendulum-v0', num_processes=1, seed=0)
        exit()
    #test()

    import Pyro4.naming
    import threading
    import time
    from tools import get_ip
    host = get_ip('eth0')
    #if host is None:
    #host = '127.0.0.1'
    host_ns = host
    def start_nameserver():
        Pyro4.naming.startNSloop(host=host, port=13579)
    threading.Thread(target=start_nameserver).start()

    def register_obj():
        Pyro4.Daemon.serveSimple(
            {
                obj: "rl_envs"
            },
            ns=True, host=host_ns, port=24680
        )
    obj = EnvServerMulti()
    threading.Thread(target=register_obj).start()

    time.sleep(1)
    with Pyro4.locateNS(host=host_ns, port=13579) as ns:
        for name,value in ns.list(prefix='').items():
            print( '{:30}'.format(name), value )
    print('Started!!!')
    exit()