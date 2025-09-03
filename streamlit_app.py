import streamlit as st
import numpy as np
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# ページ設定
st.set_page_config(
    page_title="画像のデジタル表現①デジタル化の手順",
    page_icon="🖼️",
    layout="wide"
)

# タイトルとキャプション
st.title("画像のデジタル表現①デジタル化の手順")
st.caption("Created by Dit-Lab.(Daiki ITO)")
st.caption("Supported by Tomoaki ATSUMI")

st.markdown("---")
st.markdown("""
### 📚 学習目標
このアプリケーションでは、**画像のデジタル化**がどのような手順で行われるかを可視化しながら学習します。
画像が単なる絵ではなく、**解像度**（細かさ）と**階調数**（色の深さ）によって数値データに変換される仕組みを体験的に理解しましょう。
""")

def create_demo_image():
    """デモ用の簡単な画像を生成"""
    # グラデーション画像を作成
    width, height = 200, 200
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 円形のグラデーションを作成
    center_x, center_y = width // 2, height // 2
    max_distance = np.sqrt(center_x**2 + center_y**2)
    
    for y in range(height):
        for x in range(width):
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            intensity = int(255 * (1 - distance / max_distance))
            intensity = max(0, min(255, intensity))
            
            # カラフルな円を作成
            image[y, x, 0] = intensity  # Red
            image[y, x, 1] = intensity // 2  # Green
            image[y, x, 2] = 255 - intensity  # Blue
    
    return Image.fromarray(image)

def apply_sampling(image, resolution):
    """標本化を適用（解像度を下げる）"""
    width, height = image.size
    new_width = max(1, width // resolution)
    new_height = max(1, height // resolution)
    
    # 縮小してから拡大することで標本化効果を実現
    small_image = image.resize((new_width, new_height), Image.LANCZOS)
    sampled_image = small_image.resize((width, height), Image.NEAREST)
    
    return sampled_image, (new_width, new_height)

def apply_quantization(image, levels):
    """量子化を適用（階調数を減らす）"""
    image_array = np.array(image)
    
    # 各チャンネルを指定された階調数に量子化
    quantized = np.round(image_array / 255.0 * (levels - 1)) * (255.0 / (levels - 1))
    quantized = np.clip(quantized, 0, 255).astype(np.uint8)
    
    return Image.fromarray(quantized)

def pixel_to_binary(pixel_value, bit_depth):
    """ピクセル値を2進数に変換"""
    return format(int(pixel_value * (2**bit_depth - 1) / 255), f'0{bit_depth}b')

def create_binary_visualization(image, levels, sample_size=8):
    """符号化の可視化用データを作成"""
    bit_depth = int(np.log2(levels))
    image_array = np.array(image)
    
    # グレースケールに変換
    gray_image = np.mean(image_array, axis=2) if len(image_array.shape) == 3 else image_array
    
    # サンプルピクセルを選択
    height, width = gray_image.shape
    sample_pixels = []
    
    for i in range(sample_size):
        y = (i * height) // sample_size
        x = (i * width) // sample_size
        pixel_value = gray_image[y, x]
        binary = pixel_to_binary(pixel_value, bit_depth)
        sample_pixels.append({
            'position': f'({x},{y})',
            'value': int(pixel_value),
            'binary': binary
        })
    
    return sample_pixels, bit_depth

# メイン処理開始
st.markdown("## 🖼️ 1. 画像の準備")

# 画像アップロードまたはデモデータの選択
uploaded_file = st.file_uploader("画像をアップロードしてください", type=['png', 'jpg', 'jpeg'])

use_demo = st.checkbox("デモデータを使用", value=True)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.success("アップロードされた画像を使用しています")
    use_demo = False  # アップロードされた場合はデモデータのチェックを無効化
elif use_demo:
    image = create_demo_image()
    st.success("デモデータを使用しています")
else:
    st.warning("画像をアップロードするか、デモデータのチェックボックスをオンにしてください")
    st.stop()

# 画像を表示
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(image, caption="元の画像", use_container_width=True)

st.markdown("---")

# デジタル化パラメータの設定
st.markdown("## ⚙️ 2. デジタル化パラメータの設定")
st.markdown("""
以下のパラメータを調整して、画像のデジタル化がどのように行われるかを体験してください。
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔲 解像度 (Resolution)")
    st.markdown("画像を構成するピクセルの細かさを設定します")
    resolution = st.slider(
        "解像度の分割数",
        min_value=2,
        max_value=20,
        value=8,
        step=1,
        help="数値が大きいほど、画像が粗くなります（ピクセルが大きくなります）"
    )

with col2:
    st.markdown("### 🎨 階調数 (Tonal Gradation)")
    st.markdown("各ピクセルの色の濃淡を何段階で表現するかを設定します")
    levels_options = [2, 4, 8, 16, 32, 64, 128, 256]
    levels = st.select_slider(
        "階調数",
        options=levels_options,
        value=16,
        help="数値が大きいほど、滑らかな階調表現が可能になります"
    )

# パラメータ情報の表示
bit_depth = int(np.log2(levels))
st.info(f"""
**現在の設定:**
- 解像度分割数: {resolution} (画像が{resolution}×{resolution}のブロックに分割されます)
- 階調数: {levels} ({bit_depth}ビットで表現)
""")

st.markdown("---")

# ステップ1: 標本化 (Sampling)
st.markdown("## 📐 ステップ1：標本化 (Sampling)")
st.markdown("""
**標本化**とは、連続的なアナログ信号（画像）を離散的なデジタル信号に変換する過程で、
画像を規則的な格子状の**ピクセル**に分割する処理です。
""")

# 標本化を適用
sampled_image, new_dimensions = apply_sampling(image, resolution)

col1, col2, col3 = st.columns(3)

with col1:
    st.image(image, caption="元の画像", use_container_width=True)

with col2:
    st.image(sampled_image, caption=f"標本化後 ({new_dimensions[0]}×{new_dimensions[1]} ピクセル)", use_container_width=True)

with col3:
    # Plotlyを使った格子の可視化
    original_array = np.array(image.convert('L'))  # グレースケールに変換
    height, width = original_array.shape
    
    fig = go.Figure()
    
    # 元の画像をヒートマップとして表示
    fig.add_trace(go.Heatmap(
        z=original_array,
        colorscale='gray',
        showscale=False,
        name="Original"
    ))
    
    # 格子を描画
    grid_x = np.arange(0, width, width//resolution)
    grid_y = np.arange(0, height, height//resolution)
    
    for x in grid_x:
        fig.add_vline(x=x, line=dict(color="red", width=2))
    for y in grid_y:
        fig.add_hline(y=y, line=dict(color="red", width=2))
    
    fig.update_layout(
        title="ピクセル格子の可視化",
        xaxis_title="X座標",
        yaxis_title="Y座標",
        showlegend=False,
        width=None,  # 自動調整
        height=None,  # 自動調整
        margin=dict(l=20, r=20, t=40, b=20),  # マージンを調整
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed")
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 解像度の影響を説明
st.markdown("""
### 📊 解像度の影響

- **高解像度**（分割数が少ない）: ピクセルが細かく、画像がより滑らかに見える
- **低解像度**（分割数が多い）: ピクセルが粗く、ブロック状になる

**データ量への影響**: 解像度が高いほど、より多くのピクセルが必要となり、データ量が大きくなります。
""")

st.markdown("---")

# ステップ2: 量子化 (Quantization)
st.markdown("## 🎯 ステップ2：量子化 (Quantization)")
st.markdown("""
**量子化**とは、連続的な値を離散的な値に変換する処理です。
画像処理では、各ピクセルの明度や色の値を、限られた階調数で表現できる値に丸めます。
""")

# 標本化された画像に量子化を適用
quantized_image = apply_quantization(sampled_image, levels)

col1, col2, col3 = st.columns(3)

with col1:
    st.image(sampled_image, caption="標本化後の画像", use_container_width=True)

with col2:
    st.image(quantized_image, caption=f"量子化後 ({levels}階調)", use_container_width=True)

with col3:
    # 階調の分布をヒストグラムで表示
    sampled_array = np.array(sampled_image.convert('L'))
    quantized_array = np.array(quantized_image.convert('L'))
    
    fig = go.Figure()
    
    # 元の画像のヒストグラム
    fig.add_trace(go.Histogram(
        x=sampled_array.flatten(),
        nbinsx=50,
        name="標本化後",
        opacity=0.7,
        marker_color="blue"
    ))
    
    # 量子化後のヒストグラム
    fig.add_trace(go.Histogram(
        x=quantized_array.flatten(),
        nbinsx=50,
        name="量子化後",
        opacity=0.7,
        marker_color="red"
    ))
    
    fig.update_layout(
        title="階調分布の比較",
        xaxis_title="階調値",
        yaxis_title="ピクセル数",
        height=300,
        barmode='overlay'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 階調レベルの可視化
st.markdown("### 🔢 階調レベルの詳細")

# 階調レベルをバーで表示
quantization_levels = np.linspace(0, 255, levels)
colors = [f'rgb({int(level)}, {int(level)}, {int(level)})' for level in quantization_levels]

fig = go.Figure(data=[
    go.Bar(
        x=list(range(levels)),
        y=[1] * levels,
        marker_color=colors,
        text=[f'{int(level)}' for level in quantization_levels],
        textposition='outside'
    )
])

fig.update_layout(
    title=f"{levels}階調のレベル分布",
    xaxis_title="階調レベル番号",
    yaxis_title="",
    showlegend=False,
    height=200,
    yaxis=dict(showticklabels=False)
)

st.plotly_chart(fig, use_container_width=True)

# 量子化の影響を説明
st.markdown("""
### 📈 量子化の影響

- **高階調数**: 色の変化が滑らか、グラデーションが美しく表現される
- **低階調数**: ポスタリゼーション効果（色の段差）が発生

**データ量への影響**: 階調数が多いほど、1ピクセルあたりのデータ量（ビット数）が大きくなります。
""")

st.markdown("---")

# ステップ3: 符号化 (Encoding)
st.markdown("## 💻 ステップ3：符号化 (Encoding)")
st.markdown("""
**符号化**とは、量子化された値を最終的にコンピュータが扱える**2進数（バイナリ）**のデジタルデータに変換する処理です。
各ピクセルの階調値が、0と1の組み合わせで表現されます。
""")

# サンプルピクセルの2進数変換を取得
sample_pixels, bit_depth = create_binary_visualization(quantized_image, levels)

col1, col2 = st.columns([1, 1])

with col1:
    st.image(quantized_image, caption=f"量子化済み画像 ({levels}階調)", use_container_width=True)

with col2:
    # サンプルピクセルの2進数表現をテーブルで表示
    st.markdown("### 🔢 サンプルピクセルの2進数変換")
    
    # データフレームを作成
    import pandas as pd
    
    df = pd.DataFrame(sample_pixels)
    df.columns = ['座標', '階調値', '2進数表現']
    
    # Streamlitのテーブルで表示
    st.dataframe(df, use_container_width=True, hide_index=True)

# ビット深度の説明
st.markdown(f"""
### 🧮 ビット深度の計算

現在の設定では：
- **階調数**: {levels}
- **必要なビット数**: {bit_depth}ビット
- **計算式**: log₂({levels}) = {bit_depth}

**1ピクセルあたり {bit_depth}ビット** のデータが必要になります。
""")

# 2進数変換の可視化
st.markdown("### 📊 階調値と2進数の対応関係")

# 全階調レベルの2進数を表示
all_levels = np.linspace(0, 255, levels)
binary_table_data = []

for i, level in enumerate(all_levels):
    binary_rep = format(i, f'0{bit_depth}b')
    binary_table_data.append({
        'レベル番号': i,
        '階調値': int(level),
        '2進数': binary_rep
    })

# Plotlyでバー+テキストで表示
fig = go.Figure()

fig.add_trace(go.Bar(
    x=[data['レベル番号'] for data in binary_table_data],
    y=[1] * len(binary_table_data),
    text=[f"{data['階調値']}<br>{data['2進数']}" for data in binary_table_data],
    textposition='inside',
    marker_color=[f'rgb({data["階調値"]}, {data["階調値"]}, {data["階調値"]})' 
                  for data in binary_table_data],
    textfont=dict(color='white', size=10)
))

fig.update_layout(
    title=f"{levels}階調の2進数表現一覧",
    xaxis_title="レベル番号",
    yaxis_title="",
    showlegend=False,
    height=300,
    yaxis=dict(showticklabels=False)
)

st.plotly_chart(fig, use_container_width=True)

# データ量の計算
total_pixels = new_dimensions[0] * new_dimensions[1]
total_bits = total_pixels * bit_depth
total_bytes = total_bits / 8

st.markdown(f"""
### 📈 総データ量の計算

- **画像サイズ**: {new_dimensions[0]} × {new_dimensions[1]} = {total_pixels:,}ピクセル
- **1ピクセルあたり**: {bit_depth}ビット
- **総ビット数**: {total_pixels:,} × {bit_depth} = {total_bits:,}ビット
- **総バイト数**: {total_bits:,} ÷ 8 = {total_bytes:.1f}バイト

**メモリ使用量**: 約{total_bytes/1024:.2f}KB （グレースケール単色の場合）
""")

st.markdown("---")

# まとめと考察
st.markdown("## 📋 まとめと考察")

# 全ての処理済み画像を一覧で表示
st.markdown("### 🖼️ デジタル化プロセスの全体像")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.image(image, caption="①元の画像", use_container_width=True)

with col2:
    st.image(sampled_image, caption=f"②標本化後<br>({new_dimensions[0]}×{new_dimensions[1]}px)", use_container_width=True)

with col3:
    st.image(quantized_image, caption=f"③量子化後<br>({levels}階調)", use_container_width=True)

with col4:
    # 最終的なデジタル表現を数値で示す
    final_array = np.array(quantized_image.convert('L'))
    sample_region = final_array[:8, :8]  # 8x8のサンプル領域
    
    fig = go.Figure(data=go.Heatmap(
        z=sample_region,
        colorscale='gray',
        showscale=True,
        text=sample_region,
        texttemplate="%{text}",
        textfont={"size": 8, "color": "red"}
    ))
    
    fig.update_layout(
        title="④デジタルデータ<br>(数値表現)",
        height=200,
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed")
    )
    
    st.plotly_chart(fig, use_container_width=True)

# パラメータと結果の関係性をまとめ
st.markdown("### 📊 パラメータの影響まとめ")

# 比較表を作成
comparison_data = {
    "パラメータ": ["解像度分割数", "階調数"],
    "現在の値": [f"{resolution}", f"{levels}"],
    "データ量への影響": [
        f"画像サイズ: {total_pixels:,}px",
        f"ビット深度: {bit_depth}bit/px"
    ],
    "画質への影響": [
        "分割数↑ → 画像が粗くなる" if resolution > 10 else "分割数適度 → バランス良好",
        "階調数↑ → 滑らかな表現" if levels > 32 else "階調数低 → ポスタリゼーション"
    ]
}

df_comparison = pd.DataFrame(comparison_data)
st.table(df_comparison)

# トレードオフの関係を可視化
st.markdown("### ⚖️ 画質とデータ量のトレードオフ")

# 異なる設定でのデータ量を計算
trade_off_data = []
for res in [4, 8, 12, 16, 20]:
    for lev in [4, 8, 16, 32, 64]:
        pixels = (image.width // res) * (image.height // res)
        bits = int(np.log2(lev))
        total_size = pixels * bits
        trade_off_data.append({
            'resolution': res,
            'levels': lev,
            'pixels': pixels,
            'bit_depth': bits,
            'total_bits': total_size,
            'size_label': f'解像度:{res}, 階調:{lev}'
        })

# 現在の設定をハイライト
current_data = [d for d in trade_off_data if d['resolution'] == resolution and d['levels'] == levels][0]

fig = go.Figure()

# 全データポイント
fig.add_trace(go.Scatter(
    x=[d['pixels'] for d in trade_off_data],
    y=[d['total_bits'] for d in trade_off_data],
    mode='markers',
    marker=dict(size=8, color='lightblue', opacity=0.6),
    text=[d['size_label'] for d in trade_off_data],
    name='他の設定'
))

# 現在の設定をハイライト
fig.add_trace(go.Scatter(
    x=[current_data['pixels']],
    y=[current_data['total_bits']],
    mode='markers',
    marker=dict(size=20, color='red', symbol='star'),
    text=[current_data['size_label']],
    name='現在の設定'
))

fig.update_layout(
    title="画質とデータ量のトレードオフ関係",
    xaxis_title="総ピクセル数（画質の指標）",
    yaxis_title="総データ量（ビット）",
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# 学習のポイント
st.markdown("### 🎯 学習のポイント")

st.success("""
**このアプリケーションで学んだこと：**

1. **標本化（Sampling）**: アナログ画像 → ピクセル格子への分割
   - 解像度が高い（分割数が少ない） → 滑らかな画像、大容量
   - 解像度が低い（分割数が多い） → ブロック状、軽量

2. **量子化（Quantization）**: 連続的な階調 → 離散的な階調レベル
   - 階調数が多い → 滑らかなグラデーション、大容量
   - 階調数が少ない → ポスタリゼーション効果、軽量

3. **符号化（Encoding）**: 階調値 → 2進数のデジタルデータ
   - ビット深度 = log₂(階調数)
   - データ量 = ピクセル数 × ビット深度
""")

st.info("""
**実際の応用例：**
- **Webの画像**: 高解像度・高階調（品質重視）
- **メール添付**: 中解像度・中階調（バランス重視）
- **IoTセンサー**: 低解像度・低階調（軽量化重視）
""")

# 体験を促すメッセージ
st.markdown("### 🔄 さらに体験してみよう！")
st.markdown("""
スライダーを動かして、異なる設定での画質とデータ量の変化を観察してください。
- 解像度分割数を変更 → 画像の細かさの変化を確認
- 階調数を変更 → 色の滑らかさの変化を確認
- 両方を最大・最小にして → 極端な違いを体感
""")

st.markdown("---")
st.markdown("### 🙏 謝辞")
st.markdown("""
このアプリケーションを通じて、**画像のデジタル化**の基本原理を体験的に学習できました。
デジタル画像は、解像度と階調数という2つの要素によって決まる**ピクセル**と**ビット深度**の組み合わせで
表現されるということを理解できました。
""")