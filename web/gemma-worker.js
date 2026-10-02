import { pipeline, TextStreamer, env } from '@huggingface/transformers';
env.allowLocalModels = false;
let generator;
let runtime;
const modelId='onnx-community/gemma-3-270m-it-ONNX';
// The older conversion uses a regular embedding Gather, supported by WASM.
// The newer conversion quantizes embeddings with a GPU-only operator.
const cpuRevision='cfd5c04f84a64766d63efc5bb1d2cf31f34a4a90';
const gpuRevision='2dbbfdb1b59bd034eb959428c6a7da9dd7ea27f0';
self.onmessage = async ({data}) => {
  try {
    if(!generator) {
      let adapter=null;
      try { adapter=await self.navigator.gpu?.requestAdapter(); } catch {}
      runtime=adapter?'webgpu':'wasm';
      self.postMessage({type:'status',text:`Downloading Gemma for ${runtime==='webgpu'?'GPU':'CPU'}. This first load can take a few minutes.`});
      generator=await pipeline('text-generation',modelId,{
        revision:adapter?gpuRevision:cpuRevision,
        dtype:'q4',device:runtime,progress_callback:p=>self.postMessage({type:'progress',status:p.status,file:p.file,progress:p.progress})
      });
      self.postMessage({type:'ready',runtime});
    }
    if(data.type==='load') return;
    let text='';
    const start=performance.now();
    const streamer=new TextStreamer(generator.tokenizer,{skip_prompt:true,skip_special_tokens:true,
      callback_function:chunk=>{text+=chunk;self.postMessage({type:'token',text});}});
    const output=await generator([{role:'user',content:data.prompt}],{max_new_tokens:96,do_sample:false,streamer});
    self.postMessage({type:'done',text:text || output[0].generated_text.at(-1).content,
      model:modelId,runtime,revision:runtime==='webgpu'?gpuRevision:cpuRevision,duration_ms:performance.now()-start});
  } catch(e) { self.postMessage({type:'error',text:String(e.message||e)}); }
};
