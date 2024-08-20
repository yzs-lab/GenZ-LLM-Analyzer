# Import necessary libraries
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import warnings
from GenZ import decode_moddeling, prefill_moddeling, get_configs
import pandas as pd
from tqdm import tqdm

from Systems.system_configs import system_configs

st.set_page_config(
    page_title="Model Comparisons",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/abhibambhaniya/GenZ-LLM-Analyzer/issues',
        'Report a bug': "https://github.com/abhibambhaniya/GenZ-LLM-Analyzer/issues",
        'About': "https://github.com/abhibambhaniya/GenZ-LLM-Analyzer/blob/main/README.md"
    }
)

st.sidebar.title("Model comparisons")
st.sidebar.subheader("1. Select Models to compare")
st.sidebar.subheader("2. Select Preconfigured use-case or make your customized use-case")
st.sidebar.subheader("3. Select HW System to run on")

st.sidebar.info(
    "This app is maintained by Abhimanyu Bambhaniya. ")

st.title("Compare various Model Performance")
    
# Define the function to generate the demand curve
def generate_demand_curve(system_box, system_eff, num_nodes_slider,
                        model_box, quantization_box, batch_slider,
                        input_token_slider, output_token_slider, beam_size,
                        ):
    warnings.filterwarnings("ignore")

    data = []
    mem_size_data = []
    batch_size_list = [1,2,4,8,16,32,48,64,80,96,112,128,136,144,160, 172, 180, 200, 224, 240, 256]
    for batch_size in tqdm(batch_size_list):
        for model in model_box:
            if batch_size <= batch_slider:
                model_name = get_configs(model).model
                try: 
                    prefill_outputs = prefill_moddeling(model = model, batch_size = batch_size,
                                            input_tokens = input_token_slider, output_tokens = output_token_slider, FLAT = True,
                                            system_name = system_box, system_eff = system_eff,
                                            bits=quantization_box,
                                            tensor_parallel = num_nodes_slider, debug=False, time_breakdown=True) 
                    data.append([model_name,'Prefill',batch_size, prefill_outputs['Latency'], prefill_outputs['Throughput']] + prefill_outputs['Runtime_breakdown'])
                    decode_outputs = decode_moddeling(model = model, batch_size = batch_size, Bb = beam_size ,
                                            input_tokens = input_token_slider, output_tokens = output_token_slider, FLAT = True,
                                            system_name = system_box, system_eff=system_eff,
                                            bits=quantization_box,
                                            tensor_parallel = num_nodes_slider, debug=False, time_breakdown=True) 
                    data.append([model_name,'Decode',batch_size,  decode_outputs['Latency'], decode_outputs['Throughput']] + decode_outputs['Runtime_breakdown'])
                except:
                    # ValueError
                    decode_outputs, decode_summary_table = decode_moddeling(model = model, batch_size = batch_size, Bb = beam_size ,
                                            input_tokens = input_token_slider, output_tokens = output_token_slider, FLAT = True,
                                            system_name = system_box, system_eff = system_eff,
                                            bits=quantization_box, model_profilling=True) 
                    total_memory = int(system_box.get('Memory_size'))*1024  ## per device memory
                    memory_req =  decode_summary_table['Model Weights (MB)'].values[0] + decode_summary_table['KV Cache (MB)'].values[0] 

                    mem_size_data.append([model, total_memory, batch_size, beam_size, input_token_slider, output_token_slider, np.ceil(memory_req/total_memory)])
    
    data_df = pd.DataFrame(data, columns = ['Model', 'Stage','Batch', 'Latency(ms)', 'Tokens/s', 'GEMM Time', 'Attn Time', 'Communication Time'])
    chip_req_df = pd.DataFrame(mem_size_data, columns = ['Model', 'NPU memory','Batch', 'Beam size', 'Input Tokens', 'Output Tokens', 'Min. Chips'])
    if len(data) == 0 :
        return chip_req_df
    else:
        data_df['Stage'] = pd.Categorical(data_df['Stage'], categories=['Prefill','Decode'])
        
        fig = px.line(data_df, x="Batch", y="Tokens/s",  line_group="Model", color="Model", facet_row='Stage', 
                    labels={"Batch": "Batch", "Tokens/s": "Tokens/s", "Model": "Model"},
                    width=1200, height=600, markers=True)


        # Customize axis labels
        fig.update_xaxes(title_font=dict(size=24))
        fig.update_yaxes(title_font=dict(size=24))

        # Customize tick labels
        fig.update_xaxes(tickfont=dict(size=24))
        fig.update_yaxes(tickfont=dict(size=24))
        fig.update_yaxes(matches=None)

        # # Customize facet labels
        fig.update_layout(
            font_size=24
        )

        return fig




def main():

    col1, col2, col3 = st.columns([6,3,4])

    with col1:
        st.header("Model")
        models = [
        'meta-llama/Llama-2-7B',
        'meta-llama/Meta-Llama-3.1-8B',
        'meta-llama/Llama-2-13B',
        'meta-llama/Llama-2-70B',
        'meta-llama/Meta-Llama-3.1-405B',
        'google/gemma-2B',
        'google/gemma-7B',
        'google/gemma-2-9B',
        'google/gemma-2-27B',
        'mistralai/mistral-7B',
        'mistralai/Mixtral-8x7B',
        'microsoft/phi3mini',
        'microsoft/phi3small',
        'microsoft/phi3medium',
        'databricks/dbrx-base',
        'xai-org/grok-1',
        'openai/gpt-3',
        'openai/gpt-4',
        'facebook/opt-125m',
        'facebook/opt-350m',
        'facebook/opt-1.3b',
        'facebook/opt-175b',
        ]
        selected_models = st.multiselect("Models:", models, default=models[0])
        st.markdown("""
            <style>
                .stMultiSelect [data-baseweb=select] span{
                    max-width: 250px;
                    font-size: 1rem;
                }
            </style>
            """, unsafe_allow_html=True)
        quantization = st.selectbox("Quantization:", ['bf16', 'int8', 'int4', 'int2', 'fp32'])

    with col2:
        st.header("Use case")

        max_batch_size = st.number_input("Max Batch Size:", value=8, step=1,min_value=1)
        use_case = st.selectbox("Usecases:", ['Ques-Ans', 'Text Summarization', 'Chatbots', 'Code Gen.', 'Custom'])
        if 'Ques-Ans' == use_case:
            used_beam_size = 4
            used_input_tokens = 1000
            used_output_tokens = 200
        elif 'Text Summarization' == use_case:
            used_beam_size = 4
            used_input_tokens = 15000
            used_output_tokens = 1000
        elif 'Chatbots' == use_case:
            used_beam_size = 2
            used_input_tokens = 2048
            used_output_tokens = 128
        elif 'Code Gen.' == use_case:
            used_beam_size = 4
            used_input_tokens = 20000
            used_output_tokens = 50
        beam_size = st.slider("No. of Parallel Beams:", min_value=1, max_value=16, value=used_beam_size)
        input_tokens = st.number_input("Input Tokens:", value=used_input_tokens)
        output_tokens = st.number_input("Output Tokens:", value=used_output_tokens)



    
    with col3:
        st.header("HW System")

        systems = ['A100_40GB_GPU', 'A100_80GB_GPU', 'H100_GPU','GH200_GPU', 'TPUv4','TPUv5e', 'MI300X', 'Gaudi3', 'Custom']
        selected_system = st.selectbox("System:", systems)
        nodes = st.number_input("# Nodes:", value=2, step=1)
        system_efficiency = st.slider("System Efficiency:", min_value=0.0, max_value=1.0, value=0.80, step=0.01)
        
        if selected_system in system_configs:
            current_system_config = system_configs[selected_system]
            used_flops = current_system_config.get('Flops', '')
            used_mem_bw = current_system_config.get('Memory_BW', '')
            used_mem_cap = current_system_config.get('Memory_size', '')
            used_icn_bw = current_system_config.get('ICN', '')
        flops = st.number_input("FLOPS(T):", value=used_flops)
        mem_bw = st.number_input("MEM BW(TB/s):", value=used_mem_bw)
        mem_cap = st.number_input("Mem Capacity (GBs):", value=used_mem_cap)
        icn_bw = st.number_input("ICN BW(GB/s):", value=used_icn_bw)

    # Create Plotly bar chart
    if selected_models:
        fig = generate_demand_curve(
            system_box = {'Flops': flops, 'Memory_BW': mem_bw, 'Memory_size': mem_cap, 'ICN': icn_bw , 'real_values':True},
            system_eff = system_efficiency,
            num_nodes_slider = nodes,
            model_box=selected_models,
            quantization_box=quantization,
            batch_slider=max_batch_size,
            input_token_slider=input_tokens,
            output_token_slider=output_tokens,
            beam_size = beam_size
            )
        
        if isinstance(fig, pd.DataFrame):
            st.write("Number of nodes is insufficient, please increase the nodes to fit the model")
            st.dataframe(fig)
        else:
            st.plotly_chart(fig)

    # Display some calculated metrics
    # st.subheader("Calculated Metrics")
    # st.write(f"Effective System Performance: {flops}, {mem_bw}")

if __name__ == "__main__":
    main()
