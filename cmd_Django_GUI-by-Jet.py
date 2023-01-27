#!/usr/bin/env python
# encoding: utf-8
import os
import signal
import sys
import PySimpleGUI as sg
import subprocess
import time
import threading
"""
Jet: 用于快速运行pip install和Django命令的GUI
"""

import yt_dlp
import importlib, sys

importlib.reload(sys)

APP_PATH = r"M:/OneDrive/CentriCoding/PythonProjects"
PYTHON_PATH = r"C:/Python310"
p = None  # 全局子进程
cur_thread = None  # 当前守护线程
stop_event = None  # 结束守护线程的事件
sp = None  # 全局子进行

# add from PySimpleGUI.py: https://github.com/PySimpleGUI/PySimpleGUI/issues/4982
def the_thread(window: sg.Window, sp: subprocess.Popen):
    '''
    本线程调用的函数，向指定的进程发出消息事件'-THREAD-', 并输出信息
    '''
    window.write_event_value('-THREAD-', (sp, '===THREAD STARTING==='))
    #window.write_event_value('-THREAD-', (sp, '----- STDOUT & STDERR Follows ----'))
    skip = False
    for line in sp.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').rstrip()
        print(convert(line))
        window.write_event_value('-THREAD-', (sp, line))
        window.Refresh() if window else None
        
    window.write_event_value('-THREAD-', (sp, '===THREAD DONE==='))
    
def convert(msg):
    return msg.encode("raw_unicode_escape").decode("utf-8")

    
# 用守护线程防止下载时卡死：
def runCommand2(cmd, timeout=None, window=None, cwd=None):
    # 重要的函数，运行指定进程
    
    try:
        args = cmd.split(' ')
        sp = sg.execute_command_subprocess(args[0], *args[1:], 
                                           pipe_output=True, stdin=subprocess.PIPE, cwd=cwd)
        cur_thread = threading.Thread(target=the_thread, # 调用相应的函数
                                    args=(window, sp),
                                    daemon=True)  # 需要长时间运行的程序，设置为守护线程
        cur_thread.start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt.')
        sp.send_signal(signal.SIGINT)
    except  Exception as e:
        print(f'Error {e} when execute:{cmd}')
        
        
# This function does the actual "running" of the command.  Also watches for any output. If found output is printed
def runCommand(cmd, timeout=None, window=None, cwd=None):
    global p
    # 重要的函数，运行指定进程
    nop = None # no operation
    try:
        if cwd is not None: # 指定了工作目录
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL,
                                 cwd=cwd)                                
        else:  
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL)

        output = ''
        for line in p.stdout:
            line = line.decode(errors='replace' if (sys.version_info) < (
                3, 5) else 'backslashreplace').rstrip()
            output += line
            print(line)
            window.refresh() if window else nop  # yes, a 1-line if, so shoot me
        retval = p.wait(timeout)
        return (retval, output)  # also return the output just for fun
    except Exception as e:
        print(f'Error {e} in execute:{cmd}')


def convert(msg):
    return msg.encode("raw_unicode_escape").decode("utf-8")


# add from PySimpleGUI.py: https://github.com/PySimpleGUI/PySimpleGUI/issues/4982
def the_thread(window: sg.Window, sp: subprocess.Popen):
    window.write_event_value('-THREAD-', (sp, '===THREAD STARTING==='))
    window.write_event_value('-THREAD-',
                             (sp, '----- STDOUT & STDERR Follows ----'))
    for line in sp.stdout:
        oline = line.decode().rstrip()
        window.write_event_value('-THREAD-', (sp, oline))
    window.write_event_value('-THREAD-', (sp, '===THREAD DONE==='))


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')
    if d['status'] == 'downloading':
        print('Downloading ...')
        percent = round(d['downloaded_bytes'] / d['total_bytes'], 2) * 100
        print(f'{percent}% downloaded.')


def create_exe(window, values):
    '''
    pyinstaller
    默认生成单个文件    pyinstaller  -F -w filename.py
    '''
    file_path = values['-FILE_PATH-']
    print(file_path)
    file_name = file_path.rpartition('/')[2] 
    cwd = file_path.rpartition('/')[0] 
    cmd = 'pyinstaller  -F -w ' + file_name
    print('cmd:', cmd)
    runCommand2(cmd, window=window, cwd=cwd)
     
def install_package(window, values):
    cwd = values['-PYTHON_PATH-']
    package = values['-PACKAGE-']
    command = 'pip install ' + package
    print('Run cmd:', command)
    window['-PACKAGE-'].update('')
    window.refresh()
    runCommand(command, window=window, cwd=cwd)
    print('Done')


def upgrade_package(window, values):
    cwd = values['-PYTHON_PATH-']
    package = values['-PACKAGE-']
    command = 'pip install --upgrade ' + package
    print('Run cmd:', command)
    window['-PACKAGE-'].update('')
    window.refresh()
    runCommand(command, window=window, cwd=cwd)
    print('Done')


def uninstall_package(window, values):
    cwd = values['-PYTHON_PATH-']
    package = values['-PACKAGE-']
    command = 'pip uninstall ' + package
    print('Run cmd:', command)
    window['-PACKAGE-'].update('')
    window.refresh()
    runCommand(command, window=window, cwd=cwd)
    print('Done')


def create_web_app(window, values):
    cwd = values['-APP_PATH-']
    project_name = values['-PROJECT_NAME-']
    command = 'django-admin startproject ' + project_name
    print('Run cmd:', command)
    runCommand(command, window=window, cwd=cwd)
    print('Done')


def run_web_app(window, values):
    """Jet:调用启动服务器后，会阻塞！无法再调用其它！

    Args:
        window (_type_): _description_
        values (_type_): _description_
    """
    global cur_thread, stop_event, sp
    project_name = values['-PROJECT_NAME-']
    cwd = values['-APP_PATH-'] + '/' + project_name
    print('cwd:', cwd)
    #方法一：会卡
    '''
    command = 'python manage.py runserver'
    print('Run cmd:', command)
    #指定工作目录, 与web app相应的目录对应
    runCommand(command, window=window, cwd=cwd)
    '''
    '''
    #方法二：也会卡
    sp = sg.execute_command_subprocess('python', 'manage.py', 'runserver', cwd=cwd, wait=True, pipe_output=True)
    print(sg.execute_get_results(sp)[0])
    '''
    #方法三：用守护线程，防止调用子进程运行时主程序阻塞 （对于需要在后台长时间运行的程序，非常有用！）
    args = ['python', 'manage.py', 'runserver']
    # 打印到多行文本中
    sg.cprint(*args, text_color='yellow', background_color='blue')
    #Jet注：在列表前加*号，会将列表拆分成一个一个的独立元素
    try:
        sp = sg.execute_command_subprocess(args[0],
                                        *args[1:],
                                        pipe_output=True,
                                        stdin=subprocess.PIPE,
                                        cwd=cwd)
        cur_thread = threading.Thread(target=the_thread, # 对应相应的函数
                                    args=(window, sp),
                                    daemon=True)  # 需要长时间运行的程序，设置为守护线程
        cur_thread.start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt.')
        sp.send_signal(signal.SIGINT)

def terminate_cmd(window, values):
    '''
    global p
    #p.exit()
    print('Terminate subprocess id:', p.pid)
    p.terminate() #终止子进程 p ，等于向子进程发送 SIGTERM 信号；
    print('Done.')
    '''
    global cur_thread, sp
    
    if cur_thread.is_alive():
        #TODO
        #cur_thread.exit()# 有问题，不能这么终止，
        sp.send_signal(signal.SIGTERM) # 向子进程发送信号terminate

        # sp.kill() #杀死子进程 ，等于向子进程发送 SIGKILL 信号； 执行后sp.returncode值为1
        sp.terminate()  # 终止子进程 ，等于向子进程发送 SIGTERM 信号， 执行后sp.returncode值为1
        #print('sp.is_alive:', sp.is_alive()) #没有此函数！
        print('Terminate subprocess id:', sp.pid)
    
        print('subprocess terminated，returncode：', sp.returncode)
        '''
        None —— 子进程尚未结束；
        ==0 —— 子进程正常退出；
        > 0—— 子进程异常退出，returncode对应于出错码；
        < 0—— 子进程被信号杀掉了。
        ''' 
        
        sg.cprint('subprocess terminated!', text_color='red', background_color='blue')


def DownloadGUI():
    sg.theme('Dark')

    layout = [
        [sg.Text('pip和Django快速执行助手（节约打字的时间）', size=(100, 1), font=('Any 10'))],
        [
            sg.Text('Set Python Path：'),
            sg.Input(PYTHON_PATH, size=(30, 1), key='-PYTHON_PATH-'),
            sg.FolderBrowse('Select Folder',
                            target='-PYTHON_PATH-',
                            enable_events=True)
        ],
        [
            sg.Text('pip包名：'),
            sg.Input(default_text='pygame', size=(15, 1), key='-PACKAGE-'),
            sg.Button('Install Package'),
            sg.Button('Upgrade Package'),
            sg.Button('Uninstall Package')
        ],
        [
            sg.Text('Python -> exe：'),
            sg.Input('', size=(40, 1), key='-FILE_PATH-'),
            sg.FileBrowse('Select Python File',  target='-FILE_PATH-', enable_events=True),
            sg.Button('Pyinstaller exe')
        ],
        
        [sg.Text('Django：')],
        [
            sg.Text('Web App Name:'),
            sg.Input('web1', size=(15, 1), key='-PROJECT_NAME-'),
            sg.Button('Create Web App')
        ],
        [
            sg.Text('Web App Parent Path：'),
            sg.Input(APP_PATH, size=(40, 1), key='-APP_PATH-'),
            sg.FolderBrowse('Select Folder',
                            target='-APP_PATH-',
                            enable_events=True)
        ],
        [sg.Button('Run Web App Server'),
         sg.Button('Stop Server')],
        [sg.Button('Exit', button_color=('white', 'firebrick3'))],
        [sg.Output(size=(90, 20), font='Courier 12')],  # 输出信息：方式一
        # 输出信息：方式二
        [
            sg.Multiline(
                size=(80, 20),
                write_only=True,
                key='-OUT-',
                reroute_stdout=False,
                reroute_stderr=False,
                echo_stdout_stderr=True,  # 绑定输出sg.cprint
                reroute_cprint=True,
                auto_refresh=True,
                expand_x=True,
                expand_y=True,
                font='Courier 10')
        ],
    ]

    window = sg.Window('pip&Django GUI助手',
                       layout,
                       text_justification='r',
                       default_element_size=(15, 1),
                       font=('Any 14'))

    func_dict = {
        'Install Package': install_package,
        'Upgrade Package': upgrade_package,
        'Uninstall Package': uninstall_package,
        'Create Web App': create_web_app,
        'Run Web App Server': run_web_app,
        'Stop Server': terminate_cmd,
        'Pyinstaller exe': create_exe,
    }

    while True:
        event, values = window.read()
        if event in ('Exit', None):
            break

        if event in func_dict:
            func_dict[event](window, values)

        elif event == '-THREAD-':
            #print('in event -THREAD-')
            thread_sp = values['-THREAD-'][0]
            line = values['-THREAD-'][1]
            sg.cprint(line)
            if line == '===THREAD DONE===':
                sg.cprint(f'Completed', c='white on green')

    window.close()




if __name__ == '__main__':
    DownloadGUI()
