import com.comsol.model.*;
import com.comsol.model.util.*;

/** Question 4: coupled heat/moisture transport in a uniformly shrinking cylindrical herb. */
public class Q4Automation {
  private static final String WORK_DIR =
      "D:\\26mathmodel\\CUMCM2026Problems\\A题\\comsol_q4\\near_surface_check\\original_dense";

  public static Model build() throws java.io.IOException {
    Model model = ModelUtil.create("Model");
    model.modelPath(WORK_DIR);
    model.label("q4_shrinking_herb_comsol.mph");

    model.param().set("R0", "0.02[m]", "Initial herb radius");
    model.param().set("L", "0.08[m]", "Representative cylinder length; ends insulated");
    model.param().set("hT", "25[W/(m^2*K)]", "Convective heat transfer coefficient");
    model.param().set("hm", "8e-7[m/s]", "Convective moisture transfer coefficient");

    // Temperature unknown is stored as the numerical value in degC, matching the paper equations.
    createInterpolation(model, "Te", "Te", "ambient_temperature.txt", "1");
    createInterpolation(model, "Ce", "Ce", "ambient_moisture.txt", "1");
    createInterpolation(model, "Rt", "Rt", "radius_history.txt", "m");

    model.component().create("comp1", true);
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").lengthUnit("m");
    model.component("comp1").geom("geom1").create("r1", "Rectangle");
    model.component("comp1").geom("geom1").feature("r1").set("size", new String[]{"R0", "L"});
    model.component("comp1").geom("geom1").run();

    model.component("comp1").variable().create("var1");
    model.component("comp1").variable("var1").set("Csafe", "max(C,1e-6)");
    model.component("comp1").variable("var1").set("rho", "760[kg/m^3]+90[kg/m^3]*Csafe");
    model.component("comp1").variable("var1").set("cp", "1850[J/(kg*K)]+2150[J/(kg*K)]*Csafe/(Csafe+1)");
    model.component("comp1").variable("var1").set("kherb", "0.12[W/(m*K)]+0.20[W/(m*K)]*Csafe/(Csafe+1)");
    model.component("comp1").variable("var1").set("Dherb", "4.2e-4[m^2/s]*exp(-0.30/Csafe)*exp(-3850/(T+273.15))");
    model.component("comp1").variable("var1").set("shrink", "R0/Rt(t)");
    model.component("comp1").variable("var1").set("rphys", "x*Rt(t)/R0");

    // Reference-coordinate radial PDE. x is the material radius at t=0.
    model.component("comp1").physics().create("heat", "CoefficientFormPDE", "geom1");
    model.component("comp1").physics("heat").field("dimensionless").field("T");
    model.component("comp1").physics("heat").field("dimensionless").component(new String[]{"T"});
    model.component("comp1").physics("heat").feature("cfeq1").set("da", "x*rho*cp");
    model.component("comp1").physics("heat").feature("cfeq1").set("c", "x*kherb*shrink^2");
    model.component("comp1").physics("heat").feature("cfeq1").set("f", "0");
    model.component("comp1").physics("heat").feature("init1").set("T", "28");
    model.component("comp1").physics("heat").create("flux1", "FluxBoundary", 1);
    model.component("comp1").physics("heat").feature("flux1").selection().set(4);
    model.component("comp1").physics("heat").feature("flux1").set("q", "R0*hT*shrink");
    model.component("comp1").physics("heat").feature("flux1").set("g", "R0*hT*shrink*Te(t)");

    model.component("comp1").physics().create("mass", "CoefficientFormPDE", "geom1");
    model.component("comp1").physics("mass").field("dimensionless").field("C");
    model.component("comp1").physics("mass").field("dimensionless").component(new String[]{"C"});
    model.component("comp1").physics("mass").feature("cfeq1").set("da", "x");
    model.component("comp1").physics("mass").feature("cfeq1").set("c", "x*Dherb*shrink^2");
    model.component("comp1").physics("mass").feature("cfeq1").set("f", "0");
    model.component("comp1").physics("mass").feature("init1").set("C", "2.55");
    model.component("comp1").physics("mass").create("flux1", "FluxBoundary", 1);
    model.component("comp1").physics("mass").feature("flux1").selection().set(4);
    model.component("comp1").physics("mass").feature("flux1").set("q", "R0*hm*shrink");
    model.component("comp1").physics("mass").feature("flux1").set("g", "R0*hm*shrink*Ce(t)");

    model.component("comp1").mesh().create("mesh1");
    model.component("comp1").mesh("mesh1").autoMeshSize(3);
    model.component("comp1").mesh("mesh1").run();

    model.study().create("std1");
    model.study("std1").create("time", "Transient");
    model.study("std1").feature("time").set("tlist", "range(0,600,183600) 183915.71747843814 184200");
    model.study("std1").feature("time").set("rtol", "1e-4");
    model.study("std1").run();

    double[] x = new double[1001];
    double[] y = new double[1001];
    for (int i = 0; i < 1001; i++) {
      x[i] = i * 0.00002;
      y[i] = 0.04;
    }
    model.result().dataset().create("cpt1", "CutPoint2D");
    model.result().dataset("cpt1").set("pointx", x);
    model.result().dataset("cpt1").set("pointy", y);

    model.result().create("pgC", "PlotGroup2D");
    model.result("pgC").label("Moisture field in shrinking herb reference domain");
    model.result("pgC").create("surf1", "Surface");
    model.result("pgC").feature("surf1").set("expr", "C");

    model.result().create("pgT", "PlotGroup2D");
    model.result("pgT").label("Temperature field in shrinking herb reference domain");
    model.result("pgT").create("surf1", "Surface");
    model.result("pgT").feature("surf1").set("expr", "T");

    model.result().export().create("data1", "Data");
    model.result().export("data1").set("data", "cpt1");
    model.result().export("data1").set("expr", new String[]{"T", "C", "rphys", "Rt(t)"});
    model.result().export("data1").set("descr", new String[]{"Temperature", "Moisture", "Physical radius", "Herb radius"});
    model.result().export("data1").set("filename", WORK_DIR + "\\q4_comsol_profiles.csv");
    model.result().export("data1").set("separator", ",");
    model.result().export("data1").run();

    model.save(WORK_DIR + "\\q4_shrinking_herb_comsol.mph");
    return model;
  }

  private static void createInterpolation(Model model, String tag, String name,
                                          String file, String fununit) {
    model.func().create(tag, "Interpolation");
    model.func(tag).set("funcname", name);
    model.func(tag).set("source", "file");
    model.func(tag).set("filename", WORK_DIR + "\\" + file);
    model.func(tag).set("interp", "linear");
    model.func(tag).set("argunit", "s");
    model.func(tag).set("fununit", fununit);
  }

  public static void main(String[] args) throws java.io.IOException {
    build();
  }
}
