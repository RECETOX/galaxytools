# Container image for the Galaxy OPERA tool.#
# OPERA is a MATLAB-compiled application: it needs the proprietary MathWorks MATLAB Runtime
# (v24.2, ~1.1 GB), a JRE (OpenJDK 8-11), PaDEL-Descriptor 1.00 and CDK 2.0. None of this is
# available on bioconda, so the Galaxy tool is delivered through this image (see README.rst).
#
# Build context must contain the upstream release asset OPERA2.9_CL_Par.tar.xz
# (sha256 91971dbf2ed89ca4418d44eb397eebe7592c75768d5a4aac6ce45197d685c13e), downloaded from
# https://github.com/NIEHS/OPERA/releases/tag/v2.9.5
#
# docker build -t recetox/opera:2.9.5--0 .
#
# NOTE: the MathWorks MATLAB Runtime is not MIT-licensed.

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
# OPERA itself - stripped version, with bundled KNIME software removed. Galaxy tool won't be using option requiring this software.
# The release asset is a self-extracting archive; it is unpacked to /opt/OPERA so that
# /opt/OPERA/application/run_OPERA.sh and /opt/matlab_runtime/
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
 && knime_sw="$(find /opt/OPERA -maxdepth 3 -type d -name 'knime*' | head -n1)" \
 && rm -rf "${knime_sw}" \
 && rm -rf /tmp/* /tmp/.[!.]*

 RUN run_OPERA="$(find /opt/OPERA -maxdepth 3 -type f -name 'run_OPERA.sh' | head -n1)" \
 && chmod +x "${run_OPERA}" \
 && ln -sf /opt/OPERA /usr/local/bin/OPERA

 RUN mcr_directory="$(find /opt/OPERA -maxdepth 3 -type d -name 'R2023b' | head -n1)" \
 && ln -sf "${mcr_directory}" /opt/matlab_runtime 
 
 ENV run_opera=/opt/OPERA/application/run_OPERA.sh \
    mcr_directory=/opt/matlab_runtime

WORKDIR /tmp
ENTRYPOINT []
CMD ["/opt/OPERA/application/run_OPERA.sh", "/opt/matlab_runtime", "-h"]
