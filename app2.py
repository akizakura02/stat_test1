import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

st.title('対応のない2群データの統計解析')

st.text('1行のデータ名と数値のデータ列のあるファイルを作成し、読み込ませてください。')
st.text('例: ')

df_sample = pd.DataFrame({'abcd' : [12, 13, 60, 41, 55]})
df_sample

col1, col2 = st.columns(2)
df1 : pd.DataFrame = None
df2 : pd.DataFrame = None

# CSVファイルのアップロード
uploaded_file1 = col1.file_uploader("1. CSVまたはExcelファイルをアップロードしてください", type=['csv', 'xlsx'], key='1')

# アップロードされたファイルをデータフレームに読み込む
if uploaded_file1 is not None:
    if uploaded_file1.type == 'text/csv':
            df1 = pd.read_csv(uploaded_file1)
    elif uploaded_file1.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        df1 = pd.read_excel(uploaded_file1)
    else:
        col1.text('エラー CSVまたはExcelファイルを選択してください。')

    # テーブルの表示
    col1.write("データサンプル")
    col1.write(df1.head())

# CSVファイルのアップロード
uploaded_file2 = col2.file_uploader("2. CSVまたはExcelファイルをアップロードしてください", type=['csv', 'xlsx'], key='2')

# アップロードされたファイルをデータフレームに読み込む
if uploaded_file2 is not None:
    if uploaded_file2.type == 'text/csv':
            df2 = pd.read_csv(uploaded_file2)
    elif uploaded_file2.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        df2 = pd.read_excel(uploaded_file2)
    else:
        col2.text('エラー CSVまたはExcelファイルを選択してください。')

    # テーブルの表示
    col2.write("データサンプル")
    col2.write(df2.head())

def barplot_annotate_brackets(num1, num2, data, center, 
                              height, yerr=None, dh=.05, 
                              barh=.05, fs=None, maxasterix=None):
    """ 
    Annotate barplot with p-values.
    ネットに落ちてたすんごい関数
  
    :param num1: 左のバーのインデックス番号
    :param num2: 右のバーのインデックス番号
    :param data: 注釈として書き込む文字列、またはアスタリスクを生成するための数値（p値）
    :param center: バーの中心位置
    :param height: バーの高さ
    :param yerr: 各バーの y 軸方向のエラーバー
    :param dh: バーの上の高さオフセット（0 から 1 の軸座標）
    :param barh: バーの高さ（0 から 1 の軸座標）
    :param fs: フォントサイズ
    :param maxasterix: 非常に小さい p 値に対して書くアスタリスクの最大数
    """
  
    if type(data) is str:
        text = data
    else:
        # * is p < 0.05
        # ** is p < 0.005
        # *** is p < 0.0005
        # etc.
        text = ''
        p = .05
  
        while data < p:
            text += '*'
            p /= 10.
  
            if maxasterix and len(text) == maxasterix:
                break
  
        if len(text) == 0:
            text = 'n. s.'
  
    lx, ly = center[num1], height[num1]
    rx, ry = center[num2], height[num2]
  
    if yerr:
        ly += yerr[num1]
        ry += yerr[num2]
  
    ax_y0, ax_y1 = plt.gca().get_ylim()
    dh *= (ax_y1 - ax_y0)
    barh *= (ax_y1 - ax_y0)
  
    y = max(ly, ry) + dh
  
    barx = [lx, lx, rx, rx]
    bary = [y, y+barh, y+barh, y]
    mid = ((lx+rx)/2, y+barh)
  
    plt.plot(barx, bary, c='black')
  
    kwargs = dict(ha='center', va='bottom')
    if fs is not None:
        kwargs['fontsize'] = fs
  
    plt.text(*mid, text, **kwargs)

def boxplot(df_1, df_2, p, column1, column2):
    """ plot """
    heights = [0, df_1.iloc[:,0].max(), df_2.iloc[:,0].max()]
    bars = range(0, len(heights))
    label = [column1, column2]

    plt.figure(figsize=(4, 5))
    plt.boxplot([df_1.iloc[:,0], df_2.iloc[:,0]], tick_labels=label)
    if p >0.05:
        barplot_annotate_brackets(1, 2, 'n.s.', bars, heights)
    else:
        barplot_annotate_brackets(1, 2, 'p < 0.05', bars, heights)
    st.pyplot(plt)

def analyze(df1, df2):

    df_1 = df1
    df_2 = df2
    column1 = df_1.columns[0]
    column2 = df_2.columns[0]

    shapiro_s_1, shapiro_p_1 = stats.shapiro(np.sort(df_1.iloc[:,0]))
    shapiro_s_2, shapiro_p_2 = stats.shapiro(np.sort(df_2.iloc[:,0]))

    st.text('--------------------')
    st.text('Shapiro Test')
    st.text(f'1. {column1}: {shapiro_p_1}')
    st.text(f'2. {column2}: {shapiro_p_2}')
    if shapiro_p_1 > 0.05 and shapiro_p_2 > 0.05:
        st.text('帰無仮説を採択 標本は正規分布に従う')

        # F検定
        # 帰無仮説: 母集団の分散に差がない
        # 自由度
        n1, n2 = len(df_1.iloc[:,0]), len(df_2.iloc[:,0])
        dfn, dfd = n1 - 1, n2 - 1
        # 不偏分散
        var1, var2 = stats.tvar(df_1.iloc[:,0]), stats.tvar(df_2.iloc[:,0])
        # F値は不偏分散の比率
        f_value = var1 / var2
        # p値を計算 両側検定
        f_frozen = stats.f.freeze(dfn, dfd)
        # 右側
        p1 = f_frozen.sf(f_value)
        # 左側
        p2 = f_frozen.cdf(f_value)
        # 小さい方の2倍がp値
        p_value = min(p1, p2) * 2

        st.text('F test')
        st.text(f'f: {f_value}')
        st.text(f'p: {p_value}')

        if p_value > 0.05:
            st.text('帰無仮説を採択 母集団の分散に差はない')

            # スチューデントのt検定
            student_t, student_p = stats.ttest_ind(df_1.iloc[:,0], df_2.iloc[:,0], equal_var=True)
            st.text('Student T test')
            st.text(f'p: {student_p}')

            if student_p > 0.05:
                st.text('帰無仮説を採択 2群間に有意差なし')
                boxplot(df_1, df_2, student_p, column1, column2)
            else:
                st.text('帰無仮説を棄却 2群間に有意差あり')
                boxplot(df_1, df_2, student_p, column1, column2)
        else: 
            st.text('帰無仮説を棄却 母集団の分散に差はある')

            # ウェルチのt検定
            welch_t, welch_p = stats.ttest_ind(df_1.iloc[:,0], df_2.iloc[:,0], equal_var=False)
            st.text('Welch T test')
            st.text(f'p: {welch_p}')
            
            if welch_p > 0.05:
                st.text('帰無仮説を採択 2群間に有意差なし')
                boxplot(df_1, df_2, welch_p, column1, column2)
            else:
                st.text('帰無仮説を棄却 2群間に有意差あり')
                boxplot(df_1, df_2, welch_p, column1, column2)
    else:
        st.text('帰無仮説を棄却 標本は正規分布に従わない')

        # マン・ホイットニーのＵ検定
        man_t, man_p = stats.mannwhitneyu(df_1.iloc[:,0], df_2.iloc[:,0], alternative='two-sided')
        st.text('Mannwhitney U test')
        st.text(f'p: {man_p}')

        if man_p > 0.05:
            st.text('帰無仮説を採択 2群間の代表値に有意差なし')
            boxplot(df_1, df_2, man_p, column1, column2)
        else:
            st.text('帰無仮説を棄却 2群間の代表値に有意差あり')
            boxplot(df_1, df_2, man_p, column1, column2)

if (uploaded_file1 != None) and (uploaded_file2 != None):
    st.header('読み込み成功！')
    analyze(df1, df2)