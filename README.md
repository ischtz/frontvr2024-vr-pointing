# Object Center of Mass Predicts Pointing Endpoints in Virtual Reality

This repository contains the experiment code, data, and analysis for our 2024 manuscript in *Frontiers in Virtual Reality* (Schuetz & Fiehler, 2024). 

## Abstract

Humans point using their index finger to intuitively communicate distant locations to others. This requires the human sensorimotor system to select an appropriate target location to guide the hand movement. Mid-air pointing gestures have been well studied using small and well defined targets, e.g. numbers on a wall, but how we select a specific location on a more extended 3D object is currently less well understood. In this study, participants pointed at custom 3D objects (”vases”) from different vantage points in virtual reality, allowing to estimate 3D pointing and gaze endpoints. Endpoints were best predicted by an object’s center of mass (CoM). Manipulating object meshes to shift the CoM induced corresponding shifts in pointing as well as gaze endpoints, suggesting that CoM plays a major role in guiding eye-hand alignment, at least when pointing to 3D objects in a virtual environment.


## Study Summary

![methods_tasks](https://github.com/user-attachments/assets/28be6e78-e6d2-4013-a8b1-b504521b262d)

**Paper Figure 1.** *Pointing Task Illustrations. A: Baseline accuracy task in VR, shown using sphere cursor feedback. Small green sphere (upper right) indicates the target, blue sphere serves as finger tip feedback. B: Object pointing task in VR, shown using rigid hand model feedback. C: Calibration of index finger position. Experimenter is holding a second Vive Tracker (left) whose origin point is used to calibrate the participant’s (right) index finger offset. D: Example pointing gesture using the wrist-mounted Vive Tracker.*



![objects_row](https://github.com/user-attachments/assets/ded68488-f043-4336-abaf-4ea02369e25c)

**Paper Figure 2.** *3D objects (”vases”) used in the experiment, grouped by center of mass position (high, middle, low) and rotational symmetry (symmetric, asymmetric). Colors for illustration purposes only (not corresponding to exact colors used in the experiment).*



![cog_manipulation](https://github.com/user-attachments/assets/41902e19-c3f0-4768-bebe-7c571a461244)

**Paper Figure 6.** *Effects of Center of Mass (CoM) manipulation on 3D endpoints. A: X and Y coordinates of average 3D endpoints, shown by vertical CoM position (high, middle, low) and horizontal symmetry (diamond: symmetric, circle: asymmetric). Dotted vertical line indicates symmetric object midline. B: Linear mixed model results (estimated marginal means) for vertical (Y) endpoint position, shown by vertical CoM position and horizontal symmetry. C: Linear mixed model results (estimated marginal means) for horizontal (X) endpoint position, shown for the same factors as in B. X coordinates for middle CoM objects were inverted (cf. A) to align signs. Error bars in all plots denote ± 1 SEM. Data shown for cursor feedback method and left eye pointing vectors only. Significant effects only labeled for vertical CoM comparisons, please refer to Results for other effects.* 



🛠 This study also used our experiment toolbox for the Vizard platform. [Check it out here!](https://github.com/ischtz/vizard-experiment-toolbox)



## Citation

If you use any data or code from this repository, please cite the corresponding manuscript: 

*Citation tbd*

Citation in BibTeX format:

```
[to be added]
```
