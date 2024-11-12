import streamlit as st
import subprocess
import tempfile
import os
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_api_key_input(key_name, env_var_name):
    """创建API key输入框并处理其逻辑"""
    # 直接从.env文件读取值
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env_value = ""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith(f"{env_var_name} ="):
                    env_value = line.split('=')[1].strip()
                    break

    # 创建密码输入框
    api_key = st.text_input(
        f"{key_name} API Key",
        value=env_value,
        type="password",
        help=f"Enter your {key_name} API key"
    )

    # 如果用户输入了新的API key且与环境变量不同
    if api_key and api_key != env_value:
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

            # 查找并更新API key
            key_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{env_var_name} ="):
                    lines[i] = f"{env_var_name} = {api_key}\n"
                    key_found = True
                    break

            if not key_found:
                lines.append(f"{env_var_name} = {api_key}\n")

            # 写入更新后的内容
            with open(env_path, 'w') as f:
                f.writelines(lines)
        else:
            # 如果.env文件不存在，创建新文件
            with open(env_path, 'w') as f:
                f.write(f"{env_var_name} = {api_key}\n")

        # 更新环境变量
        os.environ[env_var_name] = api_key

    return api_key

def create_api_base_input(key_name, env_var_name):
    """创建API base URL输入框并处理其逻辑"""
    # 直接从.env文件读取值
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env_base_url = ""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith(f"{env_var_name} ="):
                    env_base_url = line.split('=')[1].strip()
                    break

    # 创建base URL输入框
    api_base = st.text_input(
        f"{key_name} API Base URL",
        value=env_base_url,
        help=f"Enter your {key_name} API base URL (optional)"
    )

    # 如果用户输入了新的API base且与环境变量不同
    if api_base and api_base != env_base_url:
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

            # 查找并更新API base
            base_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{env_var_name} ="):
                    lines[i] = f"{env_var_name} = {api_base}\n"
                    base_found = True
                    break

            if not base_found:
                lines.append(f"{env_var_name} = {api_base}\n")

            # 写入更新后的内容
            with open(env_path, 'w') as f:
                f.writelines(lines)
        else:
            # 如果.env文件不存在，创建新文件
            with open(env_path, 'w') as f:
                f.write(f"{env_var_name} = {api_base}\n")

        # 更新环境变量
        os.environ[env_var_name] = api_base

    return api_base

def load_workflows():
    workflows = []
    config_dir = os.path.join(current_dir, 'config')
    for file in os.listdir(config_dir):
        if file.endswith('.yaml'):
            workflows.append(file.replace('.yaml', ''))
    return workflows

def load_config(workflow):
    config_path = os.path.join(current_dir, 'config', f'{workflow}.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Streamlit app

# 设置页面标题和图标，布局，初始侧边栏状态，菜单项
st.set_page_config(
    page_title="Text Processing Workflow",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)
# 隐藏右上角的Deploy按钮
hide_deploy_button_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
# st.markdown(hide_deploy_button_style, unsafe_allow_html=True)

st.title('Text Processing Workflow')

# API Keys section in sidebar
with st.sidebar:
    st.header('API Keys')

    # 添加OpenAI设置
    st.subheader('OpenAI Settings')
    openai_api_key = create_api_key_input("OpenAI", "OPENAI_API_KEY")
    create_api_base_input("OpenAI", "OPENAI_API_BASE")
    # openrouter_api_key = create_api_key_input("OpenRouter", "OPENROUTER_API_KEY")

    # 添加搜索工具设置
    st.header('Search Tools Settings')
    exa_api_key = create_api_key_input("EXA", "EXA_API_KEY")

# Workflow selection
workflows = load_workflows()
selected_workflow = st.selectbox('Select Workflow', workflows)

# Load config for selected workflow
config = load_config(selected_workflow)

# File uploader
uploaded_file = st.file_uploader("Upload a txt or markdown file", type=["txt", "md"])

# Text input
input_text = ""

if uploaded_file is not None:
    # Read the file content
    input_text = uploaded_file.read().decode("utf-8")

input_text = st.text_area('Enter text to process', value=input_text)

# 初始化会话状态
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'process' not in st.session_state:
    st.session_state.process = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'output_content' not in st.session_state:
    st.session_state.output_content = None

# 创建两个按钮的容器
col1, col2 = st.columns(2)

with col1:
    # Process按钮
    process_button = st.button(
        'Process', 
        disabled=st.session_state.processing or not input_text,  # 确保处理过程中禁用
        key='process_button_new',
        use_container_width=True
    )

with col2:
    # Stop按钮
    if st.session_state.processing:
        stop_button = st.button(
            'Stop', 
            key='stop_button',
            type='secondary',
            use_container_width=True
        )
        if stop_button and st.session_state.process:
            # 终止子进程
            st.session_state.process.terminate()
            st.session_state.process.wait()
            st.session_state.processing = False
            st.session_state.process = None
            st.session_state.result = None
            st.session_state.output_content = None
            st.rerun()

def process_file():
    """处理文件的函数"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
        temp_file.write(input_text)
        temp_file_path = temp_file.name

    try:
        # Prepare command with full path to app.py
        app_path = os.path.join(current_dir, 'app.py')
        cmd = ['poetry', '--directory', current_dir, 'run', 'python', app_path, temp_file_path, '--workflow', selected_workflow, '--debug']

        # 使用Popen启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        st.session_state.process = process
        
        # 等待进程完成
        stdout, stderr = process.communicate()
        
        # 检查输出文件
        output_file = os.path.join(os.path.dirname(temp_file_path), f'{selected_workflow}-output.md')
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                st.session_state.output_content = f.read()
            st.session_state.result = "success"
        else:
            st.session_state.result = "error"
            st.session_state.output_content = f"标准输出:\n{stdout}\n\n错误输出:\n{stderr}"
            
    except Exception as e:
        st.session_state.result = "error"
        st.session_state.output_content = f"发生错误: {str(e)}\n\n"
        if 'stdout' in locals():
            st.session_state.output_content += f"标准输出:\n{stdout}\n\n"
        if 'stderr' in locals():
            st.session_state.output_content += f"错误输出:\n{stderr}"
    
    finally:
        # 清理临时文件
        os.unlink(temp_file_path)
        st.session_state.processing = False
        st.session_state.process = None

# 处理逻辑
if process_button and input_text:
    st.session_state.processing = True
    st.session_state.result = None
    st.session_state.output_content = None
    st.rerun()

if st.session_state.processing:
    with st.spinner('Processing...'):
        process_file()
        st.rerun()

# 显示结果
if st.session_state.result == "success" and st.session_state.output_content:
    st.success("处理完成！")
    st.text_area('Output', st.session_state.output_content, height=300)
    st.download_button(
        'Download Output',
        st.session_state.output_content,
        file_name=f'{selected_workflow}-output.md'
    )
elif st.session_state.result == "error" and st.session_state.output_content:
    st.error("处理过程中发生错误！")
    st.text_area('Error Details', st.session_state.output_content, height=300)