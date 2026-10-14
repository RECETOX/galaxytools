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
 curl \
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
# MATLAB Runtime v24.2.
# Downloaded from MathWorks at build time rather than committed, so that no MathWorks
# binary is redistributed inside this repository. The MCR installer supports
# unattended installation with -mode silent -agreeToLicense yes.
# ---------------------------------------------------------------------------
ARG MCR_VERSION=v242
ARG MCR_INSTALLER_URL=https://ssd.mathworks.com/supportfiles/downloads/R2024b/Release/24.2/deployment_files/installer/complete/glnxa64/MATLABRuntimeR2024b_glnxa64.zip
RUN mkdir -p /opt/matlab_runtime/${MCR_VERSION} /tmp/mcr \
 && curl -fSL "${MCR_INSTALLER_URL}" -o /tmp/mcr/mcr.zip \
 && unzip -q /tmp/mcr/mcr.zip -d /tmp/mcr \
 && /tmp/mcr/installer/install_glnxa64.sh -mode silent -agreeToLicense yes \
 -destinationFolder /opt/matlab_runtime/${MCR_VERSION} \
 && rm -rf /tmp/mcr

ENV MCR_ROOT=/opt/matlab_runtime/${MCR_VERSION} \
 LD_LIBRARY_PATH=/opt/matlab_runtime/${MCR_VERSION}/runtime:/opt/matlab_runtime/${MCR_VERSION}/bin/glnxa64:/opt/matlab_runtime/${MCR_VERSION}/sys/os/glnxa64:/opt/matlab_runtime/${MCR_VERSION}/sys/opencsv/glnxa64

# ---------------------------------------------------------------------------
# OPERA itself (parallel build: the Galaxy wrapper passes -P ${GALAXY_SLOTS}).
# The release asset is a self-extracting archive; it is unpacked to /opt/OPERA so that
# /opt/OPERA/run_OPERA.sh and /opt/matlab_runtime/v242
# match the @RUN_SCRIPT@ / @MCR_DIR@ tokens in macros.xml.
# ---------------------------------------------------------------------------
COPY OPERA2.9_CL_Par.tar.xz /tmp/
RUN tar -xJf /tmp/OPERA2.9_CL_Par.tar.xz -C /tmp \
 && mkdir -p /opt/OPERA \
 && ( \
 # Self-extracting installer if present, otherwise a plain directory tree.
 installer="$(find /tmp -maxdepth 3 -type f -name 'install' | head -n1)" ; \
 if [ -n "${installer}" ] ; then \
 chmod +x "${installer}" ; \
 "${installer}" -i silent -f /tmp/installer.properties || \
 "${installer}" --accept-solicitation-license --destination /opt/OPERA ; \
 else \
 src="$(find /tmp -maxdepth 2 -type d -name 'OPERA*' | head -n1)" ; \
 cp -a "${src}/." /opt/OPERA/ ; \
 fi \
 ) \
 && chmod +x /opt/OPERA/run_OPERA.sh \
 && rm -rf /tmp/* /tmp/.[!.]*

# PaDEL-Descriptor 1.00 and CDK 2.0 are bundled inside the OPERA installer; nothing else to add.
WORKDIR /tmp
ENTRYPOINT []
CMD ["/opt/OPERA/run_OPERA.sh", "/opt/matlab_runtime/v242", "-h"]
