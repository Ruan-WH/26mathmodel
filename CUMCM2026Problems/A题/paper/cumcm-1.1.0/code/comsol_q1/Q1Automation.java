// File: comsol_q1/Q1Automation.java
import com.comsol.model.*;
import com.comsol.model.util.*;

/** COMSOL reproduction of CUMCM 2026 A, question 1. */
public class Q1Automation {
  private static final String DEFAULT_WORK_DIR =
      "D:\\COMSOL\\test";

  public static Model run() throws java.io.IOException {
    return build(DEFAULT_WORK_DIR);
  }

  public static Model build(String workDir) throws java.io.IOException {
    Model model = ModelUtil.create("Model");
    model.modelPath(workDir);
    model.label("q1_comsol_model.mph");

    model.param().set("rad0", "0.02[m]", "Herb radius");
    model.param().set("L", "0.001[m]", "Short insulated axial slice");
    model.param().set("alphaT", "0.36/(820*2600)[m^2/s]", "Thermal diffusivity");
    model.param().set("betaT", "25/(820*2600)[m/s]", "Normalized heat transfer coefficient");
    model.param().set("hm", "8e-7[m/s]");

    model.func().create("Te", "Interpolation");
    model.func("Te").set("funcname", "Te");
    model.func("Te").set("source", "file");
    model.func("Te").set("filename", workDir + "\\ambient_temperature.txt");
    model.func("Te").set("interp", "linear");
    model.func("Te").set("argunit", "s");

    model.func().create("Ce", "Interpolation");
    model.func("Ce").set("funcname", "Ce");
    model.func("Ce").set("source", "file");
    model.func("Ce").set("filename", workDir + "\\ambient_moisture.txt");
    model.func("Ce").set("interp", "linear");
    model.func("Ce").set("argunit", "s");

    model.component().create("comp1", true);
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").lengthUnit("m");
    model.component("comp1").geom("geom1").create("r1", "Rectangle");
    model.component("comp1").geom("geom1").feature("r1").set("size", new String[]{"rad0", "L"});
    model.component("comp1").geom("geom1").run();

    model.component("comp1").variable().create("var1");
    model.component("comp1").variable("var1").set("Dmoist", "7e-9[m^2/s]*exp(-0.89/max(C,1e-6))");

    model.component("comp1").physics().create("heat", "CoefficientFormPDE", "geom1");
    model.component("comp1").physics("heat").field("dimensionless").field("T");
    model.component("comp1").physics("heat").field("dimensionless").component(new String[]{"T"});
    model.component("comp1").physics("heat").feature("cfeq1").set("da", "x");
    model.component("comp1").physics("heat").feature("cfeq1").set("c", "x*alphaT");
    model.component("comp1").physics("heat").feature("cfeq1").set("f", "0");
    model.component("comp1").physics("heat").feature("init1").set("T", "28");
    model.component("comp1").physics("heat").create("flux1", "FluxBoundary", 1);
    model.component("comp1").physics("heat").feature("flux1").selection().set(4);
    model.component("comp1").physics("heat").feature("flux1").set("g", "rad0*betaT*Te(t)");
    model.component("comp1").physics("heat").feature("flux1").set("q", "rad0*betaT");

    model.component("comp1").physics().create("mass", "CoefficientFormPDE", "geom1");
    model.component("comp1").physics("mass").field("dimensionless").field("C");
    model.component("comp1").physics("mass").field("dimensionless").component(new String[]{"C"});
    model.component("comp1").physics("mass").feature("cfeq1").set("da", "x");
    model.component("comp1").physics("mass").feature("cfeq1").set("c", "x*Dmoist");
    model.component("comp1").physics("mass").feature("cfeq1").set("f", "0");
    model.component("comp1").physics("mass").feature("init1").set("C", "2.55");
    model.component("comp1").physics("mass").create("flux1", "FluxBoundary", 1);
    model.component("comp1").physics("mass").feature("flux1").selection().set(4);
    model.component("comp1").physics("mass").feature("flux1").set("g", "rad0*hm*Ce(t)");
    model.component("comp1").physics("mass").feature("flux1").set("q", "rad0*hm");

    model.component("comp1").mesh().create("mesh1");
    model.component("comp1").mesh("mesh1").autoMeshSize(2);
    model.component("comp1").mesh("mesh1").run();

    model.study().create("std1");
    model.study("std1").create("time", "Transient");
    model.study("std1").feature("time").set("tlist", "0 100 300 600 900 1200 1500 1800");
    model.study("std1").feature("time").set("rtol", "1e-5");
    model.study("std1").run();

    double[] radii = new double[21];
    double[] axial = new double[21];
    for (int i = 0; i < 21; i++) {
      radii[i] = i * 0.001;
      axial[i] = 0.0005;
    }
    model.result().dataset().create("cpt1", "CutPoint2D");
    model.result().dataset("cpt1").set("pointx", radii);
    model.result().dataset("cpt1").set("pointy", axial);

    model.result().dataset().create("cln1", "CutLine2D");
    model.result().dataset("cln1").set("genpoints", new double[][]{{0.0, 0.0005}, {0.02, 0.0005}});

    model.result().create("pgT", "PlotGroup1D");
    model.result("pgT").label("Temperature radial profile at 1800 s");
    model.result("pgT").set("data", "cln1");
    model.result("pgT").set("looplevel", new int[]{8});
    model.result("pgT").create("lngr1", "LineGraph");
    model.result("pgT").feature("lngr1").set("expr", "T");
    model.result("pgT").feature("lngr1").set("descr", "Temperature (degC numeric)");
    model.result("pgT").feature("lngr1").set("linewidth", "2");

    model.result().create("pgC", "PlotGroup1D");
    model.result("pgC").label("Moisture radial profile at 1800 s");
    model.result("pgC").set("data", "cln1");
    model.result("pgC").set("looplevel", new int[]{8});
    model.result("pgC").create("lngr1", "LineGraph");
    model.result("pgC").feature("lngr1").set("expr", "C");
    model.result("pgC").feature("lngr1").set("descr", "Moisture (kg/kg numeric)");
    model.result("pgC").feature("lngr1").set("linewidth", "2");

    model.result().create("pgT2", "PlotGroup2D");
    model.result("pgT2").label("Temperature field at 1800 s");
    model.result("pgT2").set("looplevel", new int[]{8});
    model.result("pgT2").create("surf1", "Surface");
    model.result("pgT2").feature("surf1").set("expr", "T");

    model.result().create("pgC2", "PlotGroup2D");
    model.result("pgC2").label("Moisture field at 1800 s");
    model.result("pgC2").set("looplevel", new int[]{8});
    model.result("pgC2").create("surf1", "Surface");
    model.result("pgC2").feature("surf1").set("expr", "C");
    model.result().export().create("data1", "Data");
    model.result().export("data1").set("data", "cpt1");
    model.result().export("data1").set("expr", new String[]{"T", "C"});
    model.result().export("data1").set("descr", new String[]{"Temperature", "Moisture"});
    model.result().export("data1").set("filename", workDir + "\\q1_comsol_profiles.csv");
    model.result().export("data1").set("separator", ",");
    model.result().export("data1").run();

    model.save(workDir + "\\q1_comsol_model_with_plots.mph");
    return model;
  }

  public static void main(String[] args) throws java.io.IOException {
    String workDir = args != null && args.length > 0 ? args[0] : DEFAULT_WORK_DIR;
    build(workDir);
  }
}
