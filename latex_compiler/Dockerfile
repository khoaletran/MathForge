# Dockerfile cho LaTeX Compiler Microservice
FROM texlive/texlive:latest

WORKDIR /workdir

# Cài đặt thêm các gói phông tiếng Việt và công cụ nếu cần
RUN tlmgr update --self && \
    tlmgr install babel-vietnamese vntex cm-super xcolor pgf

# Sao chép gói ex_test.sty vào thư mục texmf
COPY ex_test.sty /usr/share/texmf/tex/latex/ex_test/ex_test.sty
RUN mktexlsr

CMD ["pdflatex", "--version"]
