import unittest, sys, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from neuro import dataset,split_subjects,preprocess,quality,spectrum,TinyCNN

class ResearchTests(unittest.TestCase):
    def test_no_subject_leakage(self):
        x,y,ids=dataset();m,g=split_subjects(ids)
        for a,b in [('train','validation'),('train','test'),('validation','test')]:
            self.assertFalse(set(g[a]) & set(g[b]))
            self.assertFalse(np.any(m[a]&m[b]))
        self.assertTrue(np.all(m['train']|m['validation']|m['test']))
        self.assertEqual(len(x),576)
        for mask in m.values():self.assertEqual(sum(y[mask]==0),sum(y[mask]==1))

    def test_gradient_finite_difference(self):
        model=TinyCNN(12);x=np.random.default_rng(7).normal(size=(3,8,256));y=np.array([0,1,0])
        loss,grad=model.loss_grad(x,y)
        for key,index in [('kernel',(2,3,4)),('kernel',(7,1,16)),('bias',(1,)),('head',(2,1)),('head_bias',(1,))]:
            original=model.p[key][index];eps=1e-5
            model.p[key][index]=original+eps;plus=model.loss_grad(x,y)[0]
            model.p[key][index]=original-eps;minus=model.loss_grad(x,y)[0]
            model.p[key][index]=original
            self.assertAlmostEqual((plus-minus)/(2*eps),grad[key][index],places=6)

    def test_psd_energy_and_peak(self):
        wave=np.tile(10*np.sin(2*np.pi*10*np.arange(256)/128),(8,1));f,p=spectrum(wave)
        self.assertEqual(f[p.argmax()],10);self.assertAlmostEqual(p.sum()*.5,50)

    def test_preprocessing_is_per_window(self):
        x,y,ids=dataset(subjects=2,windows=2)
        self.assertTrue(np.allclose(preprocess(x)[0],preprocess(x[0])))
        self.assertTrue(np.allclose(preprocess(x).mean(axis=-1),0,atol=1e-12))

    def test_quality_and_finite_validation(self):
        x,y,ids=dataset(subjects=1,windows=2);self.assertTrue(quality(x[0])['usable'])
        x[0,0,:]=0;self.assertFalse(quality(x[0])['usable'])
        x[1,0,0]=np.nan;self.assertFalse(quality(x[1])['usable'])
        with self.assertRaises(ValueError):preprocess(x)

    def test_packaged_report_recomputes_from_exported_weights(self):
        x,y,ids=dataset();mask,groups=split_subjects(ids)
        saved=json.loads((ROOT/'models/tinycnn.json').read_text())
        report=json.loads((ROOT/'reports/synthetic-benchmark.json').read_text())
        model=TinyCNN();model.p={k:np.array(v) for k,v in saved['parameters'].items()}
        actual=(model.forward(preprocess(x[mask['test']])).argmax(axis=1)==y[mask['test']]).mean()
        self.assertAlmostEqual(actual,report['cnn']['accuracy'])
        self.assertEqual(sum(p.size for p in model.p.values()),1114)

if __name__=='__main__':unittest.main()
