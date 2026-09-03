FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        biber \
        chktex \
        fonts-noto-cjk \
        latexmk \
        lmodern \
        texlive-fonts-recommended \
        texlive-lang-chinese \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-latex-recommended \
        texlive-pictures \
        texlive-science \
        texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["latexmk", "-v"]
