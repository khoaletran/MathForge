"""
File mẫu gói ex_test.sty chuẩn của giáo viên Toán Việt Nam.
Cung cấp các môi trường: ex, bt, choice, choiceTF, shortans, loigiai, True.
Tự động bố trí phương án A, B, C, D vừa vặn trang A4 và chống ngắt đôi câu hỏi.
"""
EX_TEST_STY_CONTENT = r"""\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{ex_test}[2025/01/01 Goi lenh soan de thi trac nghiem Toan THPT]

\RequirePackage{ifthen}
\RequirePackage{amsmath,amssymb}
\RequirePackage{multicol}
\RequirePackage{enumitem}
\RequirePackage{calc}

\newcounter{excounter}
\setcounter{excounter}{0}

\newcommand{\True}{\textbf{\textsf{[Đúng]}} }
\newcommand{\loigiai}[1]{\par\noindent\textbf{\textit{Lời giải:}}\par #1\vspace{0.5em}}

\newenvironment{ex}{%
  \refstepcounter{excounter}%
  \par\penalty -200\vspace{0.5em}\noindent\textbf{Câu \theexcounter.} %
}{%
  \par\vspace{0.3em}%
}

\newenvironment{bt}{%
  \refstepcounter{excounter}%
  \par\penalty -200\vspace{0.5em}\noindent\textbf{Bài \theexcounter.} %
}{%
  \par\vspace{0.3em}%
}

% Tự động đo chiều dài để phân phối phương án A, B, C, D thành 4 cột, 2 cột hoặc 1 cột
\newlength{\choice@wd}
\newlength{\choice@maxwd}
\newcommand{\choice}[4]{%
  \par\vspace{0.2em}%
  \nopagebreak%
  \settowidth{\choice@maxwd}{\textbf{A.}~#1}%
  \settowidth{\choice@wd}{\textbf{B.}~#2}%
  \ifdim\choice@wd>\choice@maxwd \setlength{\choice@maxwd}{\choice@wd}\fi%
  \settowidth{\choice@wd}{\textbf{C.}~#3}%
  \ifdim\choice@wd>\choice@maxwd \setlength{\choice@maxwd}{\choice@wd}\fi%
  \settowidth{\choice@wd}{\textbf{D.}~#4}%
  \ifdim\choice@wd>\choice@maxwd \setlength{\choice@maxwd}{\choice@wd}\fi%
  \noindent%
  \ifdim\choice@maxwd<0.22\linewidth% 1 hàng 4 cột
    \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}llll}%
      \textbf{A.}~#1 & \textbf{B.}~#2 & \textbf{C.}~#3 & \textbf{D.}~#4%
    \end{tabular*}%
  \else\ifdim\choice@maxwd<0.46\linewidth% 2 hàng 2 cột
    \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}ll}%
      \textbf{A.}~#1 & \textbf{B.}~#2 \\%
      \textbf{C.}~#3 & \textbf{D.}~#4%
    \end{tabular*}%
  \else% 4 hàng 1 cột
    \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}l}%
      \textbf{A.}~#1 \\%
      \textbf{B.}~#2 \\%
      \textbf{C.}~#3 \\%
      \textbf{D.}~#4%
    \end{tabular*}%
  \fi\fi%
  \par\vspace{0.2em}%
}

\newcommand{\choiceTF}[4]{%
  \par\vspace{0.2em}%
  \nopagebreak%
  \begin{enumerate}[label=\textbf{\alph*)}, leftmargin=1.8em, itemsep=0.1em, topsep=0.1em]
    \item #1
    \item #2
    \item #3
    \item #4
  \end{enumerate}%
}

\newcommand{\shortans}[1]{%
  \par\vspace{0.2em}\nopagebreak\noindent\textbf{Đáp số:} \framebox[2.5cm]{\rule{0pt}{1.2em}\textbf{#1}}\par
}
"""
