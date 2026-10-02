import { pipeline, TextStreamer, env } from '@huggingface/transformers';
env.allowLocalModels = false;
let generator;
self.onmessage = async ({data}) => {
  try {
    if(!generator) {
      self.postMessage({type:'status',text:'Downloading Gemma. This first load can take a few minutes.'});
      generator=await pipeline('text-generation','onnx-community/gemma-3-270m-it-ONNX',{
        dtype:'q8',device:'wasm',progress_callback:p=>self.postMessage({type:'progress',status:p.status,file:p.file,progress:p.progress})
      });
      self.postMessage({type:'ready'});
    }
    if(data.type==='load') return;
    let text='';
    const start=performance.now();
    const streamer=new TextStreamer(generator.tokenizer,{skip_prompt:true,skip_special_tokens:true,
      callback_function:chunk=>{text+=chunk;self.postMessage({type:'token',text});}});
    const output=await generator([{role:'user',content:data.prompt}],{max_new_tokens:160,do_sample:false,streamer});
    self.postMessage({type:'done',text:text || output[0].generated_text.at(-1).content,
      model:'onnx-community/gemma-3-270m-it-ONNX',duration_ms:performance.now()-start});
  } catch(e) { self.postMessage({type:'error',text:String(e.message||e)}); }
};
