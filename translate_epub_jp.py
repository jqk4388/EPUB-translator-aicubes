import json
import os
import re
import time
import hashlib
import requests
import sys
import tkinter as tk
from tkinter import filedialog
import zipfile
from bs4 import BeautifulSoup
import shutil
from tqdm import tqdm

# from epub_conversion.utils import open_book, convert_epub_to_lines

# 函数：获取密钥
def get_secret_key(app_key, param, ts):
    md5 = hashlib.md5()
    md5.update((app_key + param + ts).encode())
    return md5.hexdigest()

# 函数：翻译文本
def translate_text(text, from_lang, to_lang):
    url = 'https://translate.10jqka.com.cn/translateApi/batch/v2/get/result'
    app_id = 'app_id'
    app_key = 'app_key'
    ts = str(int(time.time()*1000))
    text_list = [text]
    data = {
        'secretKey': get_secret_key(app_key, json.dumps({'textList': text_list, 'appId': app_id, 'from': from_lang, 'to': to_lang, 'domain': 'default'}), ts),
        'ts': ts,
        'param': json.dumps({
            'textList': text_list,
            'appId': app_id,
            'from': from_lang,
            'to': to_lang,
            'domain': 'default'
        })
    }
    headers = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        result = json.loads(response.text)
        if result['code'] != '0':
            data = json.loads(result['data'])
            return data['trans_result'][0]['dst']        
        else:
            print('翻译失败: ' + result['note'])
    else:
        print('请求失败: ' + str(response.status_code))

#文字处理，断句防止字数超过4000
def limit_text_length(text, max_length=4000):
    # 先使用 strip() 方法去除字符串两侧的空白字符
    text = text.strip()

    # 创建正则表达式，匹配句子末尾的句号（可能带有空格）或感叹号或问号
    pattern = re.compile(r'(?<=\S)([.!?。！？]\s*)')

    # 用正则表达式来切分字符串，将每个句子独立处理
    sentences = pattern.split(text)

    # 对每个句子进行处理，让其长度不超过 max_length 个字符
    result = ''
    current_length = 0
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length <= max_length:
            # 如果加上当前句子长度不超过 max_length，则拼接到结果字符串中，并累加长度
            result += sentence
            current_length += sentence_length
        else:
            # 否则，先在前一个句子的末尾加上换行符，然后将当前句子拼接到结果字符串中，并重置长度计数器
            result = result.rstrip() + '\n' + sentence
            current_length = sentence_length

    # 最后，将结果字符串返回
    return result

# 函数：翻译epub文件
def translate_epub(file_path, from_lang, to_lang):
    def get_lines_from_epub(file_path):
        # 解压epub文件
        with zipfile.ZipFile(file_path) as zf:
            extract_dir = f"{file_path}_extract"
            zf.extractall(extract_dir)

        # 读取所有html文件并提取内容,删除日语ruby
        lines = []
        html_files = sorted([f"{extract_dir}/{name}" for name in zf.namelist() if name.endswith(".html") or name.endswith(".xhtml")])

        for html_file in html_files:
            with open(html_file, encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                ruby_tags = soup.find_all('ruby')
                for ruby_tag in ruby_tags:
                    # 如果<ruby>标签中包含<rb>标签
                    if ruby_tag.rb is not None:
                        rb_content = ruby_tag.rb.string.strip() # 提取出<rb>标签内的文本
                        ruby_tag.replace_with(rb_content) # 用文本替换整个<ruby>标签
                    # 否则删除<rt>标签，保留<ruby>标签剩下的内容
                    else:
                        rt_tags = ruby_tag.find_all('rt')
                        for rt_tag in rt_tags:
                            rt_tag.decompose()

                # print(soup.get_text(strip=True, separator="\n"))
                # text = soup.get_text(strip=True)

                    text = soup.get_text() # 获取BeautifulSoup解析后的文本
                    lines = text.splitlines() # 按行分割成字符串列表
                    clean_lines = [line.strip() for line in lines if line.strip()] # 删除多余的空行，并去除每行两端的空白
                    clean_text = '\n'.join(clean_lines) # 将干净的字符串列表重新拼接成一个字符串，每行之间用换行符分隔
                    result = limit_text_length(clean_text, max_length=4000)
                    lines.extend(result.split("\n"))

        # 删除临时解压文件
        shutil.rmtree(extract_dir)
        return lines

    lines = get_lines_from_epub(file_path)  # 获取文件内容并将其转换为字符
    # print(lines)
    txt_path = os.path.splitext(file_path)[0] + '.txt'

    # 获取保存进度的文件路径
    progress_file = os.path.splitext(file_path)[0] + '_progress.txt'
    try:
        with open(progress_file, 'r') as f:
            # 读取上一次保存的进度条位置
            position = int(f.read())
    except FileNotFoundError:
        position = 0

    with open(txt_path, 'a', encoding='utf-8') as f:  # 以追加模式打开文件
        for i, line in enumerate(tqdm(lines[position:])):  # 将 tqdm 放在最外层循环中，显示翻译进度条
            line = re.sub(r'<[^>]*>', '', line)
            if len(line.strip()) > 0:
                result = translate_text(line, from_lang, to_lang)
                time.sleep(0.1)
                f.write(result + '\n')

            # 保存当前进度条位置
            with open(progress_file, 'w') as p:
                p.write(str(i + position))

    # 删除进度条文件
    if os.path.exists(progress_file):
        os.remove(progress_file)

    print('翻译成功。结果已保存到 ' + txt_path)

# 主函数
def main():
    if sys.platform == 'win32':
        slash = '\\'
    else:
        slash = '/'
    
    print("请选择一个日语epub文件打开")
    root = tk.Tk()
    root.withdraw() # 隐藏窗口
    file_path = filedialog.askopenfilename() # 打开文件对话框
    print("正在翻译")
    from_lang = 'ja'
    to_lang = 'zh'
    translate_epub(file_path, from_lang, to_lang)
    input()

if __name__ == '__main__':
    main()