# Container image for the Galaxy OPERA tool.#
# OPERA is a MATLAB-compiled application: it needs the proprietary MathWorks MATLAB Runtime
# (v24.2, ~1.1 GB), a JRE (OpenJDK 8-11), PaDEL-Descriptor 1.00 and CDK 2.0. None of this is
# available on bioconda, so the Galaxy tool is delivered through this image (see README.rst).
#
# Build context must contain the upstream release asset OPERA2.9_CL_Par.tar.xz
# (sha256 91971dbf2ed89ca4418d44eb397eebe7592c75768d5a4aac6ce45197d685c13e), downloaded from
# https://github.com/NIEHS/OPERA/releases/tag/v2.9.5
#
# docker build -t quay.io/recetox/opera:2.9.5--0 .
#
# NOTE: the MathWorks MATLAB Runtime is not MIT-licensed. Review the MCR redistribution terms and
# host the resulting image in an institutional quay.io organisation before publishing.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
 LANG=C.UTF-8 \
 LC_ALL=C.UTF-8

# JRE for PaDEL/CDK, plus the X-less libs the MATLAB Runtime needs to start headless.
RUN apt-get update && apt-get install -y --no-install-recommends \
 ca-certificates \
 wget \
 openjdk-11-jre-headless \
 unzip \
 xz-utils \
 libxext6 \
 libxft2 \
 libxmu6 \
 libxt6 \
 libnss3 \
 libasound2 \
 libgtk-3-0 \
 fontconfig \
 desktop-file-utils \
 && rm -rf /var/lib/apt/lists/

# ---------------------------------------------------------------------------
# MATLAB Runtime installation (optional)

# OPERA installer installs the MATLAB runtime if not found so we don't need this in the dockerfile. 
# If you want to install it manually, uncomment the following lines and change the version and URL as needed. 
# ----------------------------------------------------------------------------   
# ARG MCR_VERSION=v242
# ARG MCR_INSTALLER_URL=https://ssd.mathworks.com/supportfiles/downloads/R2024b/Release/10/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2024b_Update_10_glnxa64.zip
# RUN mkdir -p /opt/matlab_runtime/${MCR_VERSION} /tmp/mcr \
#  && curl -fSL "${MCR_INSTALLER_URL}" -o /tmp/mcr/mcr.zip \
#  && unzip -q /tmp/mcr/mcr.zip -d /tmp/mcr \
#  && /tmp/mcr/install -mode silent -agreeToLicense yes \
#  -destinationFolder /opt/matlab_runtime/${MCR_VERSION} \
#  && rm -rf /tmp/mcr

# ENV MCR_ROOT=/opt/matlab_runtime/${MCR_VERSION} \
#  LD_LIBRARY_PATH=/opt/matlab_runtime/${MCR_VERSION}/runtime:/opt/matlab_runtime/${MCR_VERSION}/bin/glnxa64:/opt/matlab_runtime/${MCR_VERSION}/sys/os/glnxa64:/opt/matlab_runtime/${MCR_VERSION}/sys/opencsv/glnxa64

# ---------------------------------------------------------------------------
# OPERA itself (parallel build: the Galaxy wrapper passes -P ${GALAXY_SLOTS}).
# The release asset is a self-extracting archive; it is unpacked to /opt/OPERA so that
# /opt/OPERA/run_OPERA.sh and /opt/matlab_runtime/v242
# match the @RUN_SCRIPT@ / @MCR_DIR@ tokens in macros.xml.
# ---------------------------------------------------------------------------
RUN wget https://github.com/NIEHS/OPERA/releases/download/v2.9.5/OPERA2.9_CL.tar.xz  -O /tmp/OPERA2.9_CL_Par.tar.xz \
 && tar -xJf /tmp/OPERA2.9_CL_Par.tar.xz -C /tmp \
 && mkdir -p /opt/OPERA \
 && ( \
 # Self-extracting installer if present, otherwise a plain directory tree.
 installer="$(find /tmp -maxdepth 3 -type f -name '*install' | head -n1)" ; \
 if [ -n "${installer}" ] ; then \
 chmod +x "${installer}" ; \
 "${installer}" -destinationFolder /opt/OPERA -agreeToLicense yes ; \
 else \
 src="$(find /tmp -maxdepth 2 -type d -name 'OPERA*' | head -n1)" ; \
 cp -a "${src}/." /opt/OPERA/ ; \
 fi \
 ) \
 && rm -rf /tmp/* /tmp/.[!.]*

 RUN run_OPERA="$(find /opt/OPERA -maxdepth 3 -type f -name 'run_OPERA.sh' | head -n1)" \
 && chmod +x "${run_OPERA}" 

 RUN mcr_directory="$(find /opt/OPERA -maxdepth 3 -type d -name 'R2023b' | head -n1)" \
 && ln -sf "${mcr_directory}" /opt/matlab_runtime 
 
 ENV run_opera=/opt/OPERA/application/run_OPERA.sh \
    mcr_directory=/opt/matlab_runtime

WORKDIR /tmp
ENTRYPOINT []
CMD ["/opt/OPERA/application/run_OPERA.sh", "/opt/matlab_runtime", "-h"]
