---
title: "Lab_Answers"
source: "https://chatgpt.com/c/69b78698-0600-832b-9841-b269f21e4c3b"
---

# Operator Questions — Runtime Lab Observability

These questions define the functional requirements of the dashboard.  
The system is complete when an operator can answer these questions within seconds without consulting logs or external tools.

The purpose is not visual completeness but **operational truthfulness**.

---


## 1\. Model Reality Questions

These verify that the runtime environment matches the intended configuration.

Questions the system must answer:

• What model actually loaded?  
• Which runtime engine loaded it?  
• What dtype is the model actually using?  
• What quantization method is active?  
• What attention implementation is active?  
• What context length is actually configured?  
• Did the runtime silently change any of the above?

Evidence sources must include:

• model metadata panel  
• load truth JSON  
• backend configuration capture

Failure cases that must be detectable:

• dtype promotion  
• incorrect quantization path  
• partial CPU offload  
• mismatched model path

---

## 2\. GPU State Questions

These verify the physical GPU state during runtime.

Questions the system must answer:

• What is the GPU doing right now?  
• How much VRAM is allocated vs reserved vs free?  
• Is the GPU compute pipeline saturated?  
• Is memory bandwidth saturated?  
• Is the GPU throttling or power limited?  
• Is the model fully resident in VRAM?

The operator must be able to determine:

compute bound  
memory bound  
idle  
blocked

The system must expose a **360-degree GPU view** equivalent to an extended `nvidia-smi`.

Required signals:

• VRAM used  
• VRAM reserved  
• VRAM free  
• GPU utilization  
• SM occupancy  
• memory bandwidth utilization  
• power draw  
• temperature

---

## 3\. Memory Integrity Questions

These verify that runtime memory behavior matches expectations.

Questions the system must answer:

• Is the model fully loaded into VRAM?  
• Is memory fragmentation occurring?  
• Is PyTorch reserving more memory than expected?  
• Is KV cache allocation correct?  
• Is memory being swapped to host?  
• Is any unexpected offloading occurring?

The system must detect:

hidden CPU offload  
GPU swap  
cache overflow  
allocator fragmentation

Evidence must come from:

• torch allocator metrics  
• GPU memory metrics  
• KV cache metrics

---

## 4\. KV Cache Questions

These determine whether attention memory is behaving correctly.

Questions the system must answer:

• How large is the KV cache?  
• How much of it is currently used?  
• Is the KV cache filling up?  
• Is the cache fragmented?  
• Are sequences being evicted?  
• Is context size limiting performance?

Operators must be able to determine:

cache underutilized  
cache saturated  
cache thrashing

---

## 5\. Throughput Questions

These measure raw inference speed.

Questions the system must answer:

• How many tokens per second are being produced?  
• Is that number stable or fluctuating?  
• What is the effective tokens/sec including latency?  
• Is batching working?  
• Is throughput scaling with batch size?

The dashboard must distinguish:

raw generation speed  
effective request speed

---

## 6\. Latency Questions

These reveal pipeline bottlenecks.

Questions the system must answer:

• What is the time to first token?  
• What is prefill latency?  
• What is decode latency?  
• What is the full request latency?  
• Where is latency accumulating?

Operators must be able to infer:

attention bottleneck  
KV bandwidth bottleneck  
queue delay  
token sampling overhead

---

## 7\. Request Flow Questions

These track inference workload behavior.

Questions the system must answer:

• How many requests are active?  
• Are requests queueing?  
• Is batching occurring?  
• Are requests finishing successfully?

Operators must be able to determine:

idle  
queue saturated  
batch limited  
engine stalled

---

## 8\. Turn-Level Questions

These verify individual generation results.

Questions the system must answer:

• What did the last turn produce?  
• How many tokens were generated?  
• Why did generation stop?  
• Did streaming occur correctly?

The system must expose:

• recent turns  
• token counts  
• stop reason

---

## 9\. Truth and Debug Questions

These ensure every observation can be verified.

Questions the system must answer:

• What raw data produced this metric?  
• What backend event produced this state?  
• What timestamp did it occur at?  
• What configuration produced this run?

Every panel must link to a raw truth source:

raw JSON  
backend logs  
runtime events

---

## 10\. Bottleneck Diagnosis Questions

These synthesize the previous metrics.

Questions the system must answer:

• What is currently limiting performance?

Possible diagnoses:

compute bound  
memory bound  
kv cache bound  
queue bound  
unknown

The dashboard does not need to compute the diagnosis automatically, but the signals required to infer it must be visible.

---

## 11\. Experiment Comparison Questions

These support tuning workflows.

Questions the system must answer:

• Did a configuration change improve performance?  
• Which engine performs better?  
• Which quantization method performs better?  
• Which context size is optimal?

Operators must be able to compare runs using:

tokens/sec  
latency  
VRAM usage  
cache efficiency

---

## Review Rule

Every meaningful dashboard surface must improve at least one operator question.

If a change does not directly answer a question, it must either:

• reduce ambiguity around a question  
• expose raw truth required to validate an answer

Panels that do not satisfy either condition are not required.

---

## Definition of Done

The runtime lab observability system is complete when:

• a model can be launched from the runner  
• runtime behavior can be observed live  
• performance bottlenecks can be diagnosed without external tools  
• configuration truth can be verified without reading logs  
• experiments can be compared with measurable metrics
