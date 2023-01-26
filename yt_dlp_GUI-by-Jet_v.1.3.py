#!/usr/bin/env python
# encoding: utf-8
import sys
import PySimpleGUI as sg
import subprocess
import time
import threading
import signal
#pip install  pyperclip
import pyperclip #使用Windows粘贴板 2022-11-21 adds
"""
替代youtube-dl.exe的yt-dlp的GUI界面工具。
只需复制youtube的链接，就可选择下载字幕、视频或音频。
2022-02-17:
-用Demon解决下载时卡的感觉

"""
#youtube_executable = 'path/to/youtube-dl'
# Jet modified 
import yt_dlp  # need to install yt-dlp and set PATH
import importlib,sys
importlib.reload(sys)

#youtube_executable =r"youtube-dl"  # 弃用，因下载速度受限，太慢

noconfig = ' --ignore-config '   # Don't load any more configuration files
proxy = ' socks5://127.0.0.1:7890 ' # 加上本地代理(如果用默认配置，就不用加了)， 可在GUI上修改
is_proxy = True  # 默认使用默认代理

#yt_dlp_cmd = r'C:/Python310/Scripts/yt-dlp.exe'
# C:\Python310\Scripts\yt-dlp.conf            
default_url = "https://www.youtube.com/watch?v=iuYlGRnC7J8"
#default_url = "https://youtu.be/kzSxscrubgU?list=RDkzSxscrubgU"
#default_url = "https://www.youtube.com/watch?v=5MgBikgcWnY"  # 测试多个字幕
#default_url = "https://www.youtube.com/watch?v=YlQ_4604Xfg"  # 测试自动字幕
#SAVE_PATH = r"M:/download"
SAVE_PATH = r"d:/download"

outtmpl = SAVE_PATH + r'/%(title)s.%(ext)s'  # 对应命令行参数-o "%(title)s.%(ext)s" 
''' 或者配置：
    ydl_opts = {
        'format': 'bestaudio',
        'proxy': proxy,
        'outtmpl':SAVE_PATH + '/%(title)s.%(ext)s',
        'output': 'M:\download',  # -o 不起作用！
        #'P': 'M:\download'  #不起作用！
        }
'''
yt_dlp_cmd = r'yt-dlp' + noconfig

wirte_subs = ' --write-subs '
# need to download and and aira2c folder to PATH
# https://github.com/aria2/aria2/releases
# aria2-1.36.0-win-64bit-build1.zip
# 解压缩之后把路径添加到系统PATH中

# aria2 是一个轻量级的多协议和多源命令行下载实用程序
aria2c_downloader = " --external-downloader aria2c "  

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
        
        # Jet：不打印无关的字幕信息（很长，如果都打印，有的视频可能需要几十秒！）节约运行时间
        if 'captions' in line:
            skip = True
            #print('skip information about captions...')
            msg = 'skip information about captions...'
            window.write_event_value('-THREAD-', (sp, msg))
            continue
        if skip and 'Available subtitles for ' not in line:
            continue
        if '[download] ' in line:
            pass  #TODO: 如何让显示下载进度的多行信息只显示在一行？
        skip = False
        print(line)
        #print(convert(line))  # 会有NoneType异常！
        window.write_event_value('-THREAD-', (sp, line))
        window.Refresh() if window else None
        
    window.write_event_value('-THREAD-', (sp, '===THREAD DONE==='))
    

# 用守护线程防止下载时卡死：
def runCommand2(cmd, timeout=None, window=None):
    # 重要的函数，运行指定进程
    
    try:
        args = cmd.split(' ')
        sp = sg.execute_command_subprocess(args[0], *args[1:], pipe_output=True, stdin=subprocess.PIPE)
        cur_thread = threading.Thread(target=the_thread, # 调用相应的函数
                                    args=(window, sp),
                                    daemon=True)  # 需要长时间运行的程序，设置为守护线程
        cur_thread.start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt.')
        sp.send_signal(signal.SIGINT)
    except  Exception as e:
        print(f'Error {e} when execute:{cmd}')
        

#'''
def runCommand(cmd, timeout=None, window=None):
    # 重要的函数，运行指定进程
    try:
        #p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  
        # 生成exe运行时出错 File "subprocess.py", line 1267, in _get_handles OSError: [WinError 6] 句柄无效。修改为下面：
        '''
        shell参数为False时，命令需要通过列表的方式传入；当shell为True时，可直接传入命令.
        '''
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        output = ''
        skip = False
        for line in p.stdout:
            line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').rstrip()
            # Jet：不打印无关的字幕信息（很长，如果都打印，有的视频可能需要几十秒！）节约运行时间
            if 'captions' in line:
                skip = True
                print('skip information about captions...')
                continue
            if skip and 'Available subtitles for ' not in line:
                continue
            skip = False

            output += line + '\n'
            print(line)
            #print(convert(line))
            
            window.Refresh() if window else None

        retval = p.wait(timeout)
        return (retval, output)      # also return the output just for fun
    except  Exception as e:
        print(f'Error {e} when execute:{cmd}')
#'''

def convert(msg):
    #msg是bytes类型
    #return msg.encode("raw_unicode_escape").decode("utf-8")
    # str通过encode()方法可以编码为指定的bytes。
    # 再通过decode显示成中文
    #return msg.encode('utf-8').decode('utf-8')
    return msg.decode('utf-8')



def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')
    if d['status'] == 'downloading':
        print('Downloading ...')
        percent =round(d['downloaded_bytes']/d['total_bytes'], 2)*100
        print(f'{percent}% downloaded.')

 
def msg_hook(self,d):  # 钩子函数
    # 获取下载信息：
    if d['status'] == 'finished':
        print('\r', f"{d['_percent_str']}, {d['_eta_str']}", end='\n', flush=True)  # '\n'完成一行的输出
        
        print(f"下载完成{d['filename']}")
    # Jet adds:# Jet:显示下载进度
    if d['status'] == 'downloading':
        #print('Downloading ...')
        #percent =round(d['downloaded_bytes']/d['total_bytes'], 2)*100
        #print(f'{percent} % downloaded.')
        p = d['_percent_str']
        p = p.replace('%','')
        #print(d['filename'], d['_percent_str'], d['_eta_str'])
        print('\r', f"{d['_percent_str']}, {d['_eta_str']}", end='', flush=True)  # '\r'回到行首
        time.sleep(2) # 间隔刷新显示

def get_subtitles(window, values):
    print('Getting list of subtitles....')
    window.refresh()
    link = values['-LINK-']  # 获取用户输入的URL        
    command = check_proxy(yt_dlp_cmd, values) + f' --list-subs {link}'  # 获取可下载的语言字幕
    output = runCommand(command, window=window)[1]
    #'''
    # eg.Available subtitles for CkpV9pHch04:
    '''
    zu-zh-Hant      Zulu from Chinese (Traditional)                  vtt, ttml, srv3, srv2, srv1, json3

    Language Name                  Formats
    zh-Hans  Chinese (Simplified)  vtt, ttml, srv3, srv2, srv1, json3
    zh-Hant  Chinese (Traditional) vtt, ttml, srv3, srv2, srv1, json3
    '''
    lang_list = None
    selected_lang = None
    for line in output.split('\n'):
        if 'Available subtitles for' not in line:
            continue  # 过滤掉很多无用信息
        
        lang_list = [line[:11].rstrip().split(' ')[0]
                    for line in output.split('\n') if 'vtt' in line and 'from' not in line]  # 不包括两种语言之间的翻译
    #assert lang_list
    if lang_list:
        lang_list = sorted(lang_list)
        prefered_list = ['zh-CN', 'zh-Hans', 'en', 'en-US']  # 偏好语言列表，可自行添加语言代码
        for lang in prefered_list:
            if lang in lang_list:
                selected_lang = lang
        if selected_lang:
            index = lang_list.index(selected_lang)
            # window['-COMBO-SUBTITLES-'].update(values=lang_list, default_value=selected_lang)  # 会出错！
            window['-COMBO-SUBTITLES-'].update(values=lang_list, set_to_index=[index])
        else:
            selected_lang = 'auto'
            window['-COMBO-SUBTITLES-'].update(values=[selected_lang], set_to_index=0)
        print('Done')
        
    else:
        selected_lang = 'auto'
        window['-COMBO-SUBTITLES-'].update(values=[selected_lang], set_to_index=0)
        print('No subtitle found!')
    
    return lang_list


def download_video_audio_and_subtitle(window, values):
    # 下载视频和音频+字幕
    lang = values['-COMBO-SUBTITLES-'] if values['-COMBO-SUBTITLES-']  else 'auto'  
    
    print(f'Downloading Video+Audio+Subtitle for {lang}...')
    outtmpl = ' -o ' + values['-DIR_PATH-'] + '/%(title)s.%(ext)s'  if values['-DIR_PATH-'] else ' ' # 对应命令行参数-o "%(title)s.%(ext)s" 
    #command = yt_dlp_cmd + outtmpl + f' --sub-lang {lang} --write-sub {link}' # 这是Youtube-dl的参数， 不适用！
    #command = yt_dlp_cmd + outtmpl + f' --sub-langs {lang} --write-subs {link}'  # yt-dlp参数不同,字幕和视频是独立的文件！
    link = values['-LINK-']  # 获取用户输入的URL      
    if lang=='auto':  # 没有字幕的情况下，使用自动的字幕
        # --write-auto-subs        #        Write automatically generated subtitle file
        format = f' -f bv+ba/b --write-auto-subs --embed-subs '  # 合并最好的视频和音频+ 默认的字幕
    else:
        format = f' -f bv+ba/b --sub-langs {lang} --write-subs --embed-subs '  # 合并最好的视频和音频

    command = check_proxy(yt_dlp_cmd, values) + outtmpl + format + link  # --embed-subs 字幕嵌入视频中
    
    #command = yt_dlp_cmd + outtmpl + f' --sub-langs {lang}  {link}'  # yt-dlp参数与youtube-dl不同
    print('Execute cmd:', command)
    window.refresh()
    runCommand2(command, window=window)
    print('Done')


def download_subtitle_only(window, values):
     # 下载选定语言的字幕
    lang = values['-COMBO-SUBTITLES-'] if values['-COMBO-SUBTITLES-']  else 'en'  # 默认是英语字幕
    print(f'Downloading only subtitle in {lang}...')
    outtmpl = ' -o ' + values['-DIR_PATH-'] + '/%(title)s.%(ext)s'  if values['-DIR_PATH-'] else ' ' # 对应命令行参数-o "%(title)s.%(ext)s" 
    #command = yt_dlp_cmd + outtmpl + f' --sub-lang {lang} --write-sub {link}' # 这是Youtube-dl的参数
    link = values['-LINK-']  # 获取用户输入的URL        
    format = f' --write-subs  --sub-langs {lang} --skip-download '  # 只下载字幕， 不下载视频！
    command = check_proxy(yt_dlp_cmd, values) + outtmpl + format + link  # --embed-subs 字幕嵌入视频中
    
    #奇怪，也没下载字幕文件！

    print('Execute cmd:', command)
    window.refresh()
    
    runCommand2(command, window=window)
    print('Done')

def download_video(window, values):
    global yt_dlp_cmd
    #按照选择的视频和音频格式下载
    video_format = values['-COMBO-VIDEO-FORMATS-'][0:3] # 取前三位数字：视频格式代号
    video_ext = values['-VIDEO-EXT-']
    audio_format = values['-COMBO-AUDIO-FORMATS-'][0:3] if values['-COMBO-AUDIO-FORMATS-'] else 'm4a' # 取音频格式的数字代号
    # 支持的格式：best|aac|flac|mp3|m4a|opus|vorbis|wav|alac
    audio_ext = values['-AUDIO-EXT-'] if values['-AUDIO-EXT-'] else 'm4a' # 取音频格式的字母代号

    print(f'yt_dlp Downloading video format {video_ext} and audio {audio_ext}...')
    outtmpl = ' -o ' + values['-DIR_PATH-'] + '/%(title)s.%(ext)s'  # 对应命令行参数-o "%(title)s.%(ext)s" 
    #command = yt_dlp_cmd + proxy + link
    link = values['-LINK-']  # 获取用户输入的URL        

    #format = f" -f {video_format}[ext={video_ext}]+{audio_format}[ext={audio_ext}] "
    format = f" -f {video_format}[ext={video_ext}]+{audio_format} "  # 不用ext
    # Download the best mp4 video available, or the best video if no mp4 available
    # bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b 
    
    #测试打印：下载过程中的下载进度百分比
    # yt_dlp_cmd = yt_dlp_cmd + f' --progress_hooks  [{msg_hook}]'  # 测试无效，不能这么使用！

    use_aria2c = values['-ARIA2C-']
    if use_aria2c: # 调用外部下载的程序aria2, 速度更快！但等待过程“不响应”，不显示信息，体验感不好！
        command = check_proxy(yt_dlp_cmd, values)  + aria2c_downloader + outtmpl + format + link  # yt_dlp默认配置文件里加了proxy
    else:
        command = check_proxy(yt_dlp_cmd, values)  + outtmpl + format + link  # yt_dlp默认配置文件里加了proxy
    
    print('Execute cmd:', command)
    window.refresh()
    runCommand2(command, window=window)
    print('Done')

def download_best_audio_and_video(window, values):
    # 下载最好的音频和视频（官方默认）
    video_ext = values['-VIDEO-EXT-']
    print(f'yt_dlp Downloading best audio and video...')
    outtmpl = ' -o ' + values['-DIR_PATH-'] + '/%(title)s.%(ext)s'  # 对应命令行参数-o "%(title)s.%(ext)s" 
    link = values['-LINK-']  # 获取用户输入的URL        

    # Download the best mp4 video available, or the best video if no mp4 available
    format = f" -f bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b  "
    # bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b 

    #command = yt_dlp_cmd + outtmpl + f" -f bv*+ba/b {link}"  # default format selector 
    # command = check_proxy(yt_dlp_cmd, values) + outtmpl + format + link  # default format selector 
    
    use_aria2c = values['-ARIA2C-']
    if use_aria2c: # 调用外部下载的程序aria2, 速度更快！但等待过程“不响应”，不显示信息，体验感不好！
        command = check_proxy(yt_dlp_cmd, values)  + aria2c_downloader + outtmpl + format + link  # yt_dlp默认配置文件里加了proxy
    else:
        command = check_proxy(yt_dlp_cmd, values)  + outtmpl + format + link  # yt_dlp默认配置文件里加了proxy
    
    
    
    print('Execute cmd:', command)
    window.refresh()
    runCommand2(command, window=window)
    print('Done')

def check_proxy(yt_dlp_cmd, values):
    # 检查是否使用代理
    is_proxy = values['-IS-PROXY-']
    proxy = values['-PROXY-']
    #TODO: verify legal proxy
    if is_proxy and len(proxy)>0:
        return  yt_dlp_cmd + ' --proxy ' + proxy
    else:
        return yt_dlp_cmd

def paste_link(window, values): 
    # 粘贴视频链接到link文本框中
    link = pyperclip.paste()  # 获取粘贴板内容
    if "http" in link: # 是超级链接才粘贴到链接文本框中
        window['-LINK-'].update(value=link)
        
def download_audio(window, values):
    # 下载指定的音频
    audio_format = values['-COMBO-AUDIO-FORMATS-'][0:3] # 取音频格式的数字代号
    # 支持的格式：best|aac|flac|mp3|m4a|opus|vorbis|wav|alac
    audio_ext = values['-AUDIO-EXT-'] # 取音频格式的字母代号
    audio_format = audio_ext # 不用数字代号！
    print(f'yt_dlp Downloading audio in {audio_format}...')
    outtmpl = ' -o ' + values['-DIR_PATH-'] + '/%(title)s.%(ext)s'  # 对应命令行参数-o "%(title)s.%(ext)s" 
    link = values['-LINK-']  # 获取用户输入的URL    
    '''
    -x, --extract-audio         Convert video files to audio-only files
                                 (requires ffmpeg and ffprobe)

    --audio-format FORMAT     Specify audio format to convert the audio
                                 to when -x is used. Currently supported
                                 formats are: best (default) or one of
                                 best|aac|flac|mp3|m4a|opus|vorbis|wav|alac
    '''
    command = check_proxy(yt_dlp_cmd, values) + outtmpl + f" -x --audio-format {audio_format} {link}"  # default format selector 
    print('Execute cmd:', command)
    window.refresh()
    runCommand2(command, window=window)
    print('Done')

def get_video_formats(window, values):
    print('Getting list of video formats....')
    window.refresh()
    link = values['-LINK-']  # 获取用户输入的URL        
    command = check_proxy(yt_dlp_cmd, values) + f' --list-formats  {link}'  # 获取视频类型列表 or -F
    output = runCommand(command, window=window)[1]
    '''
ID  EXT   RESOLUTION FPS │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR     ASR MORE INFO
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
sb2 mhtml 48x27          │                  mhtml │ images                                      storyboard
sb1 mhtml 80x45          │                  mhtml │ images                                      storyboard
sb0 mhtml 160x90         │                  mhtml │ images                                      storyboard
139 m4a                  │    5.56MiB   48k https │ audio only          mp4a.40.5   48k 22050Hz low, m4a_dash
249 webm                 │    5.58MiB   48k https │ audio only          opus        48k 48000Hz low, webm_dash
250 webm                 │    5.88MiB   51k https │ audio only          opus        51k 48000Hz low, webm_dash
140 m4a                  │   14.76MiB  129k https │ audio only          mp4a.40.2  129k 44100Hz medium, m4a_dash
251 webm                 │   10.63MiB   93k https │ audio only          opus        93k 48000Hz medium, webm_dash
17  3gp   176x144      6 │    8.20MiB   71k https │ mp4v.20.3       71k mp4a.40.2    0k 22050Hz 144p
394 mp4   256x144     25 │    6.38MiB   55k https │ av01.0.00M.08   55k video only              144p, mp4_dash
160 mp4   256x144     25 │    3.41MiB   29k https │ avc1.4d400c     29k video only              144p, mp4_dash
278 webm  256x144     25 │    7.79MiB   68k https │ vp9             68k video only              144p, webm_dash
395 mp4   426x240     25 │    8.82MiB   77k https │ av01.0.00M.08   77k video only              240p, mp4_dash
133 mp4   426x240     25 │    5.11MiB   44k https │ avc1.4d4015     44k video only              240p, mp4_dash
242 webm  426x240     25 │    8.65MiB   75k https │ vp9             75k video only              240p, webm_dash
396 mp4   640x360     25 │   15.30MiB  134k https │ av01.0.01M.08  134k video only              360p, mp4_dash
134 mp4   640x360     25 │    8.67MiB   76k https │ avc1.4d401e     76k video only              360p, mp4_dash
18  mp4   640x360     25 │   37.25MiB  326k https │ avc1.42001E    326k mp4a.40.2    0k 44100Hz 360p
243 webm  640x360     25 │   13.95MiB  122k https │ vp9            122k video only              360p, webm_dash
397 mp4   854x480     25 │   24.37MiB  213k https │ av01.0.04M.08  213k video only              480p, mp4_dash
135 mp4   854x480     25 │   12.68MiB  111k https │ avc1.4d401e    111k video only              480p, mp4_dash
244 webm  854x480     25 │   20.13MiB  176k https │ vp9            176k video only              480p, webm_dash
398 mp4   1280x720    25 │   42.63MiB  374k https │ av01.0.05M.08  374k viddeo only              720p, mp4_dash
136 mp4   1280x720    25 │   22.68MiB  198k https │ avc1.4d401f    198k video only              720p, mp4_dash
22  mp4   1280x720    25 │ ~124.92MiB 1070k https │ avc1.64001F   1070k mp4a.40.2    0k 44100Hz 720p
247 webm  1280x720    25 │   33.76MiB  296k https │ vp9            296k video only              720p, webm_dash
399 mp4   1920x1080   25 │   70.34MiB  617k https │ av01.0.08M.08  617k video only              1080p, mp4_dash
137 mp4   1920x1080   25 │   85.58MiB  750k https │ avc1.640028    750k video only              1080p, mp4_dash
248 webm  1920x1080   25 │   85.81MiB  752k https │ vp9            752k video only              1080p, webm_dash
    '''
    video_list = [line[:19].rstrip()
                    for line in output.split('\n') if 'video only' in line] 
    # currently 3gp, aac, flv, m4a, mp3, mp4, ogg, wav, webm are supported
    # https://github.com/yt-dlp/yt-dlp#video-format-options
    window['-COMBO-VIDEO-FORMATS-'].update(values=video_list)
    index = len(video_list)-1
    window['-COMBO-VIDEO-FORMATS-'].update(set_to_index=[index])
    print('Done')


def get_audio_formats(window, values):
    print('Getting list of audio formats....')
    window.refresh()
    link = values['-LINK-']  # 获取用户输入的URL        
    command = check_proxy(yt_dlp_cmd, values) + f' -F {link}'  
    output = runCommand(command, window=window)[1]
    '''
    
ID  EXT   RESOLUTION FPS │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR     ASR MORE INFO
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
sb2 mhtml 48x27          │                  mhtml │ images                                      storyboard
sb1 mhtml 80x45          │                  mhtml │ images                                      storyboard
sb0 mhtml 160x90         │                  mhtml │ images                                      storyboard
139 m4a                  │    5.56MiB   48k https │ audio only          mp4a.40.5   48k 22050Hz low, m4a_dash
249 webm                 │    5.58MiB   48k https │ audio only          opus        48k 48000Hz low, webm_dash
250 webm                 │    5.88MiB   51k https │ audio only          opus        51k 48000Hz low, webm_dash
140 m4a                  │   14.76MiB  129k https │ audio only          mp4a.40.2  129k 44100Hz medium, m4a_dash
251 webm                 │   10.63MiB   93k https │ audio only          opus        93k 48000Hz medium, webm_dash

248 webm  1920x1080   25 │   85.81MiB  752k https │ vp9            752k video only              1080p, webm_dash

    '''
    audio_list = [line[:8].rstrip()
                    for line in output.split('\n') if 'audio only' in line] # 只获取支持的音频
    # yt-dlp支持的格式： best|aac|flac|mp3|m4a|opus|vorbis|wav|alac
    #audio_list = ['best', 'mp3', 'm4a','wav'] # 只列出最常用的音频格式
    window['-COMBO-AUDIO-FORMATS-'].update(values=audio_list)
    index = len(audio_list)-1
    window['-COMBO-AUDIO-FORMATS-'].update(set_to_index=[index])  # 默认显示最后一个音频（最好音质）
    print('Done')
    return audio_list

def DownloadGUI():
    sg.theme('Dark')

    #combobox = sg.Combo(values=['auto', ], default_value='auto', size=(12, 1), key='-COMBO-SUBTITLES-')
    combobox = sg.Combo(values=['', ], default_value='', size=(12, 1), key='-COMBO-SUBTITLES-')
    layout = [
        [sg.Text('请先安装(pip install yt-dlp) 详情参见： https://github.com/yt-dlp/yt-dlp#installation', size=(100, 1), font=('Any 12'))],
        [sg.Text('YouTube Link:'), 
         sg.Input(default_text=default_url, size=(60, 1), key='-LINK-'),
         sg.Button('Paste Link'), ],
        [sg.Checkbox('Use Proxy:', default=True, key='-IS-PROXY-'), sg.Input(default_text=proxy, size=(60, 1), key='-PROXY-')],
        
        [sg.Text('Save to path：'), sg.Input(SAVE_PATH, size=(30,1), key='-DIR_PATH-'), 
         sg.FolderBrowse('Select Folder', target='-DIR_PATH-', enable_events=True)],
        
        [sg.Button('Get Subtitle List'), sg.Text('Language Code'), 
         combobox, sg.Button('Download Subtitle Only')],
        
        [sg.Checkbox('use aria2', enable_events=True, default=False, key='-ARIA2C-'),
         sg.Button('Download Video+Audio+Subtitle'), 
         sg.Button('Download Best Audio and Video'), ],
        
        [sg.Button('Get Video Format List'), 
         #sg.Text('Video Format List:'), 
         sg.Combo(values=['', ], size=(20, 1), key='-COMBO-VIDEO-FORMATS-'), 
         # 保存的视频格式
         sg.Text('Video Extension:'),
         sg.Combo(values=['mp4','webm'], key='-VIDEO-EXT-'),  
         sg.Button('Download Video'), 
         ],
        
        [sg.Button('Get Audio Format List'), 
         #sg.Text('Audio Format List:'), 
         sg.Combo(values=['', ], size=(10, 1), key='-COMBO-AUDIO-FORMATS-'), 
         # 保存的音频格式
         sg.Text('Audio Extension:'),
         # 支持的格式：best|aac|flac|mp3|m4a|opus|vorbis|wav|alac
         sg.Combo(values=['mp3', 'm4a', 'wav'], key='-AUDIO-EXT-'),          
         sg.Button('Download Audio')],
        [sg.Button('Exit', button_color=('white', 'firebrick3'))],
        [sg.Output(size=(110, 16), background_color='black', font='Courier 10')],    # 输出信息：方式一
        # 输出信息：方式二
        [
            sg.Multiline(
                size=(90, 20),
                write_only=True,
                key='-OUT-',
                reroute_stdout=False,
                reroute_stderr=False,
                echo_stdout_stderr=True,  # 绑定输出sg.cprint
                reroute_cprint=True,
                auto_refresh=True,
                expand_x=True,
                expand_y=True,
                font='Courier 10',
                background_color='black',)
        ],
    ]

    window = sg.Window('yt_dlp GUI-加速下载Youtube音频/视频', layout,
                       text_justification='r',
                       default_element_size=(15, 1),
                       font=('Any 14'))

    func_dict ={
        'Get Subtitle List': get_subtitles,
        'Download Video+Audio+Subtitle': download_video_audio_and_subtitle,
        'Download Subtitle Only':  download_subtitle_only,
        'Download Video': download_video,
        'Download Audio': download_audio,
        'Get Video Format List': get_video_formats,
        'Get Audio Format List': get_audio_formats,        
        'Download Best Audio and Video': download_best_audio_and_video,
        'Paste Link': paste_link, # 粘贴视频链接

    }
    
    while True:
        event, values = window.read()
        if event in ('Exit', None):
            break
        
        if event in func_dict:
            func_dict[event](window, values)
            
        #与线程（会调用进程）对应的事件，输出相应信息
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


