FROM r-base:4.0.3

WORKDIR /WaveICA
RUN apt-get update -y
RUN apt install -y r-cran-devtools
RUN Rscript -e 'devtools::install_github("dengkuistat/WaveICA",host="https://api.github.com",dependencies=TRUE)'
CMD ["/bin/bash", "R"]