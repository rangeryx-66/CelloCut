#pragma once

void meshDecimationLauncher(const bool useArea, const float wgtBnd,       //hyperparams
                            const int B, const int D, const int Nv, const int Nf, const int* nvIn, const int* mfIn,  //inputs
                            const int* nv2Remove, const float* vertexIn, const int* faceIn, const float* planeIn,    //inputs
                            int* nvOut, int* mfOut, float* vertexOut, int* faceOut, int* vtReplace, int* vtMap,      //ouputs
                            bool* isDegenerate);

void combineClustersLauncher(const int nvA, const int nvB, const int* repA, const int* mapA,
                             const int* repB, const int* mapB, int* repOut, int* mapOut);

void countVertexAdjfaceLauncher(int NfIn, const int* face, const int* vtMap, int* nfcount);