"""Run from repo root: OPENBLAS_NUM_THREADS=1 python research/train.py"""
import json, hashlib, platform
from pathlib import Path
import numpy as np
from neuro import dataset, split_subjects, preprocess, TinyCNN, band_feature, metrics, spectrum

ROOT = Path(__file__).resolve().parents[1]
def save(path, value):
    (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT/path).write_text(json.dumps(value, indent=2) + '\n')

def main():
    raw, y, ids = dataset()
    masks, groups = split_subjects(ids)
    x = preprocess(raw)
    model = TinyCNN()
    rng = np.random.default_rng(2026)
    moment = {k: np.zeros_like(v) for k,v in model.p.items()}
    variance = {k: np.zeros_like(v) for k,v in model.p.items()}
    step, best_loss, best_epoch = 0, float('inf'), 0
    history = []
    train_ids = np.where(masks['train'])[0]
    for epoch in range(1, 25):
        shuffled = rng.permutation(train_ids)
        for start in range(0, len(shuffled), 32):
            batch = shuffled[start:start+32]
            _, grads = model.loss_grad(x[batch], y[batch])
            step += 1
            for key in model.p:
                moment[key] = .9*moment[key] + .1*grads[key]
                variance[key] = .999*variance[key] + .001*grads[key]**2
                m = moment[key]/(1-.9**step)
                v = variance[key]/(1-.999**step)
                model.p[key] -= .003*m/(np.sqrt(v)+1e-8)
        val_probs = model.forward(x[masks['validation']])
        val_y = y[masks['validation']]
        val_loss = float(-np.log(val_probs[np.arange(len(val_y)),val_y]+1e-12).mean())
        train_probs = model.forward(x[masks['train']])
        train_y = y[masks['train']]
        train_loss = float(-np.log(train_probs[np.arange(len(train_y)),train_y]+1e-12).mean())
        history.append({"epoch":epoch,"train_loss":train_loss,"validation_loss":val_loss})
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch
            best = {k:v.copy() for k,v in model.p.items()}
    model.p = best
    # Baseline centres are fitted on training data only.
    feature = band_feature(raw)
    centres = [float(feature[masks['train'] & (y==i)].mean()) for i in range(2)]
    test = masks['test']
    pred = model.forward(x[test]).argmax(axis=1)
    base_pred = np.abs(feature[test,None] - centres).argmin(axis=1)
    report = {"data_source":"synthetic", "clinical_validation":False,
        "seed":144,"training_shuffle_seed":2026,"generator_version":"1.0",
        "dataset_sha256":hashlib.sha256(raw.tobytes()).hexdigest(),
        "virtual_subjects":18,"windows":len(y),"split_subjects":groups,
        "training":{"epochs":24,"selected_epoch":best_epoch,"selection":"validation loss only",
                    "optimizer":"Adam","learning_rate":.003,"batch_size":32},
        "cnn":metrics(y[test], pred), "spectral_baseline":metrics(y[test], base_pred),
        "per_test_subject":[{"id":str(s),**metrics(y[ids==s],model.forward(x[ids==s]).argmax(axis=1))} for s in groups['test']],
        "history":history,"environment":{"python":platform.python_version(),"numpy":np.__version__},
        "limitations":["Artificial frequency discrimination, not a human EEG result.",
            "Single seed, three held-out virtual subjects; no clinical or BCI claim.",
            "Softmax values are uncalibrated. No mental-state inference."]}
    weights={"schema":"neuroweave.tinycnn.v1","source":"synthetic-training-only",
        "architecture":{"channels":8,"samples":256,"filters":8,"kernel":17,"stride":4,"scale_uv":20},
        "classes":["Condition A","Condition B"], "parameters":{k:v.tolist() for k,v in model.p.items()},
        "parameter_count":sum(v.size for v in model.p.values()), "baseline_centres":centres}
    save('models/tinycnn.json',weights)
    save('reports/synthetic-benchmark.json',report)
    fixtures=[]
    for idx in [480,481,512,513]:
        f,p=spectrum(raw[idx])
        fixtures.append({"samples":raw[idx].tolist(),"probabilities":model.forward(x[idx:idx+1])[0].tolist(),
            "psd":p.tolist(),"band_feature":float(feature[idx]),"label":int(y[idx])})
    save('tests/reference.json',fixtures)
    example={"schema":"neuroweave.eeg.v1","source":"synthetic","sample_rate_hz":128,
        "unit":"uV","channels":[f"C{i+1}" for i in range(8)],"samples":raw[480].round(6).tolist()}
    save('data/example-window.json',example)
    print(json.dumps({"cnn":report['cnn'],"spectral_baseline":report['spectral_baseline'],"parameters":weights['parameter_count'],"best_epoch":best_epoch}))

if __name__=='__main__': main()
