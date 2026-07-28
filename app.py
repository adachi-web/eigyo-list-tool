import streamlit as st
import requests
import csv
import io
import time
import base64
import json

# ========== 認証情報 ==========
import os
API_LOGIN = os.environ.get("DATAFORSEO_LOGIN", st.secrets.get("DATAFORSEO_LOGIN", ""))
API_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", st.secrets.get("DATAFORSEO_PASSWORD", ""))

# ========== ページ設定 ==========
st.set_page_config(
    page_title="営業リスト抽出ツール | HYN",
    page_icon="🗾",
    layout="wide",
)

# ========== カスタムCSS ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

.main { background-color: #f8f9fb; }

.hyn-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
}
.hyn-header h1 { font-size: 1.8rem; font-weight: 700; margin: 0; letter-spacing: 0.02em; }
.hyn-header p { font-size: 0.85rem; opacity: 0.7; margin: 0.3rem 0 0; }

.card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #e8ecf0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.card h3 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid #0f3460;
}

.stButton > button {
    background: linear-gradient(135deg, #0f3460, #1a6fb0) !important;
    color: white !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.9 !important; }

.result-box {
    background: #e8f5e9;
    border: 1px solid #a5d6a7;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
}
.warn-box {
    background: #fff8e1;
    border: 1px solid #ffe082;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0;
}
.split-box {
    background: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ========== データ ==========
AREAS = {
    "北海道": ["札幌市中央区","札幌市北区","札幌市東区","札幌市白石区","札幌市豊平区","札幌市南区","札幌市西区","札幌市厚別区","札幌市手稲区","札幌市清田区","旭川市","函館市","釧路市","帯広市","小樽市","北見市","苫小牧市","江別市","恵庭市","千歳市","石狩市","北広島市","登別市","伊達市","その他（直接入力）"],
    "青森県": ["青森市","八戸市","弘前市","十和田市","三沢市","むつ市","つがる市","黒石市","五所川原市","その他（直接入力）"],
    "岩手県": ["盛岡市","一関市","奥州市","花巻市","北上市","宮古市","大船渡市","久慈市","釜石市","その他（直接入力）"],
    "宮城県": ["仙台市青葉区","仙台市宮城野区","仙台市若林区","仙台市太白区","仙台市泉区","石巻市","大崎市","気仙沼市","名取市","多賀城市","塩竈市","白石市","その他（直接入力）"],
    "秋田県": ["秋田市","横手市","大館市","能代市","由利本荘市","大仙市","湯沢市","北秋田市","その他（直接入力）"],
    "山形県": ["山形市","酒田市","鶴岡市","米沢市","新庄市","天童市","上山市","村山市","長井市","その他（直接入力）"],
    "福島県": ["福島市","郡山市","いわき市","会津若松市","須賀川市","白河市","二本松市","喜多方市","南相馬市","その他（直接入力）"],
    "茨城県": ["水戸市","つくば市","日立市","土浦市","古河市","取手市","ひたちなか市","筑西市","常総市","鹿嶋市","その他（直接入力）"],
    "栃木県": ["宇都宮市","小山市","栃木市","足利市","那須塩原市","佐野市","鹿沼市","日光市","真岡市","大田原市","その他（直接入力）"],
    "群馬県": ["前橋市","高崎市","太田市","伊勢崎市","桐生市","渋川市","館林市","沼田市","藤岡市","富岡市","その他（直接入力）"],
    "埼玉県": ["さいたま市浦和区","さいたま市大宮区","さいたま市川口区","さいたま市中央区","さいたま市桜区","さいたま市南区","さいたま市見沼区","さいたま市岩槻区","川口市","川越市","所沢市","越谷市","熊谷市","春日部市","草加市","上尾市","狭山市","入間市","志木市","和光市","新座市","朝霞市","その他（直接入力）"],
    "千葉県": ["千葉市中央区","千葉市花見川区","千葉市稲毛区","千葉市若葉区","千葉市緑区","千葉市美浜区","船橋市","松戸市","市川市","柏市","八千代市","習志野市","浦安市","成田市","野田市","木更津市","市原市","流山市","我孫子市","その他（直接入力）"],
    "東京都": ["千代田区","中央区","港区","新宿区","文京区","台東区","墨田区","江東区","品川区","目黒区","大田区","世田谷区","渋谷区","中野区","杉並区","豊島区","北区","荒川区","板橋区","練馬区","足立区","葛飾区","江戸川区","八王子市","立川市","武蔵野市","三鷹市","青梅市","府中市","昭島市","調布市","町田市","小金井市","国分寺市","国立市","西東京市","その他（直接入力）"],
    "神奈川県": ["横浜市鶴見区","横浜市神奈川区","横浜市西区","横浜市中区","横浜市南区","横浜市港南区","横浜市保土ケ谷区","横浜市旭区","横浜市磯子区","横浜市金沢区","横浜市港北区","横浜市緑区","横浜市青葉区","横浜市都筑区","横浜市戸塚区","横浜市栄区","横浜市泉区","横浜市瀬谷区","川崎市川崎区","川崎市幸区","川崎市中原区","川崎市高津区","川崎市多摩区","川崎市宮前区","川崎市麻生区","相模原市緑区","相模原市中央区","相模原市南区","横須賀市","藤沢市","平塚市","茅ヶ崎市","小田原市","厚木市","大和市","その他（直接入力）"],
    "新潟県": ["新潟市北区","新潟市東区","新潟市中央区","新潟市江南区","新潟市秋葉区","新潟市南区","新潟市西区","新潟市西蒲区","長岡市","上越市","三条市","新発田市","燕市","柏崎市","その他（直接入力）"],
    "富山県": ["富山市","高岡市","射水市","魚津市","氷見市","滑川市","砺波市","小矢部市","その他（直接入力）"],
    "石川県": ["金沢市","白山市","小松市","加賀市","羽咋市","七尾市","輪島市","珠洲市","その他（直接入力）"],
    "福井県": ["福井市","越前市","坂井市","敦賀市","鯖江市","大野市","勝山市","あわら市","その他（直接入力）"],
    "山梨県": ["甲府市","富士吉田市","甲斐市","南アルプス市","中央市","笛吹市","山梨市","その他（直接入力）"],
    "長野県": ["長野市","松本市","上田市","飯田市","諏訪市","須坂市","小諸市","伊那市","駒ヶ根市","中野市","飯山市","茅野市","塩尻市","佐久市","その他（直接入力）"],
    "岐阜県": ["岐阜市","各務原市","大垣市","多治見市","可児市","美濃加茂市","関市","中津川市","羽島市","恵那市","その他（直接入力）"],
    "静岡県": ["静岡市葵区","静岡市駿河区","静岡市清水区","浜松市中央区","浜松市浜名区","浜松市天竜区","沼津市","富士市","磐田市","焼津市","藤枝市","島田市","富士宮市","掛川市","袋井市","三島市","その他（直接入力）"],
    "愛知県": ["名古屋市千種区","名古屋市東区","名古屋市北区","名古屋市西区","名古屋市中村区","名古屋市中区","名古屋市昭和区","名古屋市瑞穂区","名古屋市熱田区","名古屋市中川区","名古屋市港区","名古屋市南区","名古屋市守山区","名古屋市緑区","名古屋市名東区","名古屋市天白区","豊田市","岡崎市","一宮市","豊橋市","春日井市","小牧市","刈谷市","安城市","豊川市","西尾市","大府市","知多市","尾張旭市","その他（直接入力）"],
    "三重県": ["津市","四日市市","鈴鹿市","松阪市","桑名市","伊賀市","名張市","亀山市","伊勢市","尾鷲市","熊野市","その他（直接入力）"],
    "滋賀県": ["大津市","草津市","長浜市","彦根市","東近江市","近江八幡市","栗東市","甲賀市","野洲市","湖南市","その他（直接入力）"],
    "京都府": ["京都市上京区","京都市中京区","京都市下京区","京都市東山区","京都市山科区","京都市左京区","京都市右京区","京都市西京区","京都市伏見区","京都市南区","京都市北区","京都市向日市","宇治市","亀岡市","京田辺市","長岡京市","城陽市","向日市","その他（直接入力）"],
    "大阪府": ["大阪市都島区","大阪市福島区","大阪市此花区","大阪市西区","大阪市港区","大阪市大正区","大阪市天王寺区","大阪市浪速区","大阪市西淀川区","大阪市淀川区","大阪市東淀川区","大阪市東成区","大阪市生野区","大阪市旭区","大阪市城東区","大阪市鶴見区","大阪市阿倍野区","大阪市住之江区","大阪市住吉区","大阪市東住吉区","大阪市平野区","大阪市西成区","堺市堺区","堺市中区","堺市東区","堺市西区","堺市南区","堺市北区","堺市美原区","東大阪市","枚方市","豊中市","吹田市","高槻市","茨木市","八尾市","寝屋川市","守口市","大東市","門真市","四條畷市","交野市","その他（直接入力）"],
    "兵庫県": ["神戸市東灘区","神戸市灘区","神戸市兵庫区","神戸市長田区","神戸市須磨区","神戸市垂水区","神戸市北区","神戸市中央区","神戸市西区","姫路市","西宮市","尼崎市","明石市","加古川市","宝塚市","伊丹市","川西市","三田市","芦屋市","高砂市","加西市","その他（直接入力）"],
    "奈良県": ["奈良市","橿原市","生駒市","大和郡山市","天理市","桜井市","大和高田市","葛城市","宇陀市","香芝市","その他（直接入力）"],
    "和歌山県": ["和歌山市","田辺市","橋本市","海南市","有田市","御坊市","新宮市","紀の川市","その他（直接入力）"],
    "鳥取県": ["鳥取市","米子市","倉吉市","境港市","その他（直接入力）"],
    "島根県": ["松江市","出雲市","浜田市","益田市","大田市","安来市","その他（直接入力）"],
    "岡山県": ["岡山市北区","岡山市中区","岡山市東区","岡山市南区","倉敷市","津山市","総社市","玉野市","笠岡市","井原市","備前市","その他（直接入力）"],
    "広島県": ["広島市中区","広島市東区","広島市南区","広島市西区","広島市安佐南区","広島市安佐北区","広島市安芸区","広島市佐伯区","福山市","呉市","東広島市","尾道市","廿日市市","三原市","三次市","その他（直接入力）"],
    "山口県": ["山口市","下関市","宇部市","周南市","山陽小野田市","防府市","長門市","萩市","岩国市","光市","柳井市","その他（直接入力）"],
    "徳島県": ["徳島市","鳴門市","阿南市","吉野川市","阿波市","美馬市","その他（直接入力）"],
    "香川県": ["高松市","丸亀市","坂出市","善通寺市","観音寺市","さぬき市","東かがわ市","三豊市","その他（直接入力）"],
    "愛媛県": ["松山市","今治市","新居浜市","西条市","宇和島市","四国中央市","大洲市","伊予市","その他（直接入力）"],
    "高知県": ["高知市","南国市","四万十市","宿毛市","土佐清水市","須崎市","香南市","香美市","その他（直接入力）"],
    "福岡県": ["福岡市東区","福岡市博多区","福岡市中央区","福岡市南区","福岡市西区","福岡市城南区","福岡市早良区","北九州市門司区","北九州市若松区","北九州市戸畑区","北九州市小倉北区","北九州市小倉南区","北九州市八幡東区","北九州市八幡西区","久留米市","飯塚市","大牟田市","春日市","太宰府市","糸島市","筑紫野市","宗像市","古賀市","福津市","行橋市","柳川市","八女市","筑後市","大川市","豊前市","中間市","小郡市","大野城市","那珂川市","うきは市","宮若市","嘉麻市","朝倉市","みやま市","糟屋郡宇美町","糟屋郡篠栗町","糟屋郡志免町","糟屋郡須恵町","糟屋郡新宮町","糟屋郡久山町","糟屋郡粕屋町","遠賀郡芦屋町","遠賀郡水巻町","遠賀郡岡垣町","遠賀郡遠賀町","鞍手郡小竹町","鞍手郡鍍手町","嘉穂郡桂川町","朝倉郡筑前町","朝倉郡東峰村","三井郡大刀洗町","三潴郡大木町","八女郡広川町","田川郡香春町","田川郡添田町","田川郡糸田町","田川郡川崎町","田川郡大任町","田川郡赤村","田川郡福智町","京都郡苅田町","京都郡みやこ町","築上郡吉富町","築上郡上毛町","築上郡築上町","その他（直接入力）"],
    "佐賀県": ["佐賀市","唐津市","鳥栖市","伊万里市","武雄市","鹿島市","小城市","嬉野市","神埼市","多久市","その他（直接入力）"],
    "長崎県": ["長崎市","佐世保市","諫早市","大村市","島原市","対馬市","五島市","壱岐市","平戸市","松浦市","その他（直接入力）"],
    "熊本県": ["熊本市中央区","熊本市東区","熊本市西区","熊本市南区","熊本市北区","八代市","天草市","菊池市","合志市","山鹿市","玉名市","宇土市","阿蘇市","人吉市","荒尾市","水俣市","その他（直接入力）"],
    "大分県": ["大分市","別府市","中津市","佐伯市","日田市","臼杵市","津久見市","竹田市","豊後高田市","杵築市","宇佐市","豊後大野市","由布市","その他（直接入力）"],
    "宮崎県": ["宮崎市","都城市","延岡市","日向市","小林市","日南市","串間市","西都市","えびの市","その他（直接入力）"],
    "鹿児島県": ["鹿児島市","霧島市","薩摩川内市","鹿屋市","姶良市","出水市","日置市","指宿市","南さつま市","枕崎市","阿久根市","西之表市","垂水市","その他（直接入力）"],
    "沖縄県": ["那覇市","沖縄市","うるま市","浦添市","宜野湾市","豊見城市","名護市","糸満市","石垣市","宮古島市","南城市","その他（直接入力）"],
}

CATEGORIES = {
    "🍽️ 飲食": {"居酒屋": "居酒屋", "バー・スナック": "バー・スナック", "飲み屋・パブ": "飲み屋・パブ", "焼肉・ステーキ": "焼肉・ステーキ", "ラーメン": "ラーメン", "寿司": "寿司", "そば・うどん": "そば・うどん", "カレー": "カレー", "お好み焼き・たこ焼き": "お好み焼き・たこ焼き", "和食・料亭": "和食・料亭", "中華料理": "中華料理", "イタリアン・フレンチ": "イタリアン・フレンチ", "カフェ・喫茶店": "カフェ・喫茶店", "レストラン・食堂": "レストラン・食堂", "お弁当・宅配": "お弁当・宅配", "ファストフード": "ファストフード", "焼き鳥": "焼き鳥", "海鮮・魚料理": "海鮮・魚料理"},
    "💇 美容・エステ": {"美容院・美容室": "美容院・美容室", "理容店・床屋": "理容店・床屋", "エステ・サロン": "エステ・サロン", "ネイルサロン": "ネイルサロン", "まつげエクステ": "まつげエクステ", "リラクゼーション・マッサージ": "リラクゼーション・マッサージ", "化粧品・コスメ": "化粧品・コスメ"},
    "🏥 医療・健康": {"内科": "内科", "外科": "外科", "整形外科": "整形外科", "小児科": "小児科", "歯科": "歯科", "矯正歯科": "矯正歯科", "眼科": "眼科", "皮膚科": "皮膚科", "耳鼻咽喉科": "耳鼻咽喉科", "産婦人科": "産婦人科", "精神科・心療内科": "精神科・心療内科", "総合病院": "総合病院", "薬局・ドラッグストア": "薬局・ドラッグストア", "整体・カイロプラクティック": "整体・カイロプラクティック", "接骨院・整骨院": "接骨院・整骨院", "あん摩・はり・きゅう": "あん摩・はり・きゅう", "フィットネス・スポーツジム": "フィットネス・スポーツジム"},
    "👶 介護・保育": {"保育園・保育施設": "保育園・保育施設", "幼稚園": "幼稚園", "デイサービス": "デイサービス", "介護施設": "介護施設", "老人ホーム・特養ホーム": "老人ホーム・特養ホーム", "訪問介護": "訪問介護", "介護用品・福祉用具": "介護用品・福祉用具", "障害者支援施設": "障害者支援施設"},
    "📚 教育": {"学習塾・予備校": "学習塾・予備校", "英会話スクール": "英会話スクール", "スポーツクラブ・武道": "スポーツクラブ・武道", "音楽教室・ダンス教室": "音楽教室・ダンス教室", "習い事・カルチャースクール": "習い事・カルチャースクール", "専門学校・大学": "専門学校・大学"},
    "🔨 建設・住宅": {"建設業・工務店": "建設業・工務店", "リフォーム": "リフォーム", "解体工事": "解体工事", "電気工事": "電気工事", "管工事・水道工事": "管工事・水道工事", "塗装工事": "塗装工事", "屋根・かわら工事": "屋根・かわら工事", "内装工事": "内装工事", "外壁工事": "外壁工事", "造園・エクステリア": "造園・エクステリア", "建材・資材": "建材・資材", "防水工事": "防水工事", "シャッター・雨戸": "シャッター・雨戸"},
    "🏠 不動産": {"不動産屋・不動産取引": "不動産屋・不動産取引", "住宅管理会社": "住宅管理会社", "マンション・アパート管理": "マンション・アパート管理", "トランクルーム": "トランクルーム"},
    "🔒 セキュリティ・防災": {"セキュリティ・防犯": "セキュリティ・防犯", "消防・防災設備": "消防・防災設備", "鍵屋": "鍵屋"},
    "🚗 自動車": {"自動車販売・買取": "自動車販売・買取", "自動車整備・車検": "自動車整備・車検", "自動車修理・板金": "自動車修理・板金", "ガソリンスタンド": "ガソリンスタンド", "タイヤ・カー用品": "タイヤ・カー用品", "バイク販売・整備": "バイク販売・整備", "駐車場・パーキング": "駐車場・パーキング", "レッカー・ロードサービス": "レッカー・ロードサービス"},
    "🚚 運送・物流": {"運送会社・トラック": "運送会社・トラック", "引越し": "引越し", "宅配便": "宅配便", "倉庫業": "倉庫業", "鉄道・バス・航空": "鉄道・バス・航空"},
    "💼 ビジネスサービス": {"税理士": "税理士", "司法書士": "司法書士", "行政書士": "行政書士", "弁護士": "弁護士", "社会保険労務士": "社会保険労務士", "会計士・監査法人": "会計士・監査法人", "弁理士": "弁理士", "広告代理店": "広告代理店", "印刷・デザイン": "印刷・デザイン", "人材派遣・人材紹介": "人材派遣・人材紹介", "コンサルティング": "コンサルティング", "IT・システム開発": "IT・システム開発", "保険・証券": "保険・証券", "銀行・信用組合": "銀行・信用組合"},
    "🏪 小売・販売": {"スーパー・食品": "スーパー・食品", "コンビニ": "コンビニ", "ホームセンター": "ホームセンター", "家電量販店": "家電量販店", "ドラッグストア": "ドラッグストア", "衣料品・アパレル": "衣料品・アパレル", "書店": "書店", "リサイクルショップ": "リサイクルショップ"},
    "🏨 宿泊・観光・レジャー": {"ホテル": "ホテル", "旅館・民宿": "旅館・民宿", "観光施設": "観光施設", "ゴルフ場": "ゴルフ場", "パチンコ・ゲームセンター": "パチンコ・ゲームセンター", "カラオケ": "カラオケ"},
    "🌿 農業・環境": {"農業・農園": "農業・農園", "林業": "林業", "水産・漁業": "水産・漁業", "害虫駆除・消毒": "害虫駆除・消毒", "ごみ収集・産廃": "ごみ収集・産廃"},
    "🏭 工場・製造": {"食品製造": "食品製造", "金属・機械製造": "金属・機械製造", "化学・素材": "化学・素材", "印刷・出版": "印刷・出版", "繊維・衣料": "繊維・衣料"},
    "⚙️ その他": {"クリーニング": "クリーニング", "写真・スタジオ": "写真・スタジオ", "冠婚葬祭・葬儀": "冠婚葬祭・葬儀", "ペットサービス": "ペットサービス", "占い・風水": "占い・風水", "宗教施設": "宗教施設"},
}

CITY_DISTRICTS = {
    "札幌市": ["札幌市中央区","札幌市北区","札幌市東区","札幌市白石区","札幌市豊平区","札幌市南区","札幌市西区","札幌市厚別区","札幌市手稲区","札幌市清田区"],
    "仙台市": ["仙台市青葉区","仙台市宮城野区","仙台市若林区","仙台市太白区","仙台市泉区"],
    "さいたま市": ["さいたま市浦和区","さいたま市大宮区","さいたま市川口区","さいたま市中央区","さいたま市桜区","さいたま市南区","さいたま市見沼区","さいたま市岩槻区"],
    "千葉市": ["千葉市中央区","千葉市花見川区","千葉市稲毛区","千葉市若葉区","千葉市緑区","千葉市美浜区"],
    "横浜市": ["横浜市鶴見区","横浜市神奈川区","横浜市西区","横浜市中区","横浜市南区","横浜市港南区","横浜市保土ケ谷区","横浜市旭区","横浜市磯子区","横浜市金沢区","横浜市港北区","横浜市緑区","横浜市青葉区","横浜市都筑区","横浜市戸塚区","横浜市栄区","横浜市泉区","横浜市瀬谷区"],
    "川崎市": ["川崎市川崎区","川崎市幸区","川崎市中原区","川崎市高津区","川崎市多摩区","川崎市宮前区","川崎市麻生区"],
    "相模原市": ["相模原市緑区","相模原市中央区","相模原市南区"],
    "新潟市": ["新潟市北区","新潟市東区","新潟市中央区","新潟市江南区","新潟市秋葉区","新潟市南区","新潟市西区","新潟市西蒲区"],
    "静岡市": ["静岡市葵区","静岡市駿河区","静岡市清水区"],
    "浜松市": ["浜松市中央区","浜松市浜名区","浜松市天竜区"],
    "名古屋市": ["名古屋市千種区","名古屋市東区","名古屋市北区","名古屋市西区","名古屋市中村区","名古屋市中区","名古屋市昭和区","名古屋市瑞穂区","名古屋市熱田区","名古屋市中川区","名古屋市港区","名古屋市南区","名古屋市守山区","名古屋市緑区","名古屋市名東区","名古屋市天白区"],
    "京都市": ["京都市上京区","京都市中京区","京都市下京区","京都市東山区","京都市山科区","京都市左京区","京都市右京区","京都市西京区","京都市伏見区","京都市南区","京都市北区"],
    "大阪市": ["大阪市都島区","大阪市福島区","大阪市此花区","大阪市西区","大阪市港区","大阪市大正区","大阪市天王寺区","大阪市浪速区","大阪市西淀川区","大阪市淀川区","大阪市東淀川区","大阪市東成区","大阪市生野区","大阪市旭区","大阪市城東区","大阪市鶴見区","大阪市阿倍野区","大阪市住之江区","大阪市住吉区","大阪市東住吉区","大阪市平野区","大阪市西成区"],
    "堺市": ["堺市堺区","堺市中区","堺市東区","堺市西区","堺市南区","堺市北区","堺市美原区"],
    "神戸市": ["神戸市東灘区","神戸市灘区","神戸市兵庫区","神戸市長田区","神戸市須磨区","神戸市垂水区","神戸市北区","神戸市中央区","神戸市西区"],
    "岡山市": ["岡山市北区","岡山市中区","岡山市東区","岡山市南区"],
    "広島市": ["広島市中区","広島市東区","広島市南区","広島市西区","広島市安佐南区","広島市安佐北区","広島市安芸区","広島市佐伯区"],
    "北九州市": ["北九州市門司区","北九州市若松区","北九州市戸畑区","北九州市小倉北区","北九州市小倉南区","北九州市八幡東区","北九州市八幡西区"],
    "福岡市": ["福岡市東区","福岡市博多区","福岡市中央区","福岡市南区","福岡市西区","福岡市城南区","福岡市早良区"],
    "熊本市": ["熊本市中央区","熊本市東区","熊本市西区","熊本市南区","熊本市北区"],
}

SNS_DOMAINS = ['instagram.com', 'twitter.com', 'x.com', 'tiktok.com', 'youtube.com', 'line.me', 'linkedin.com']
PORTAL_DOMAINS = ['facebook.com', 'japoncompany.business', 'tabelog.com', 'hotpepper.jp', 'gnavi.co.jp', 'jalan.net', 'rakuten.co.jp', 'tripadvisor.jp', 'retty.me', 'yelp.com', 'gurunavi.com', 'yahoo.co.jp', 'kakaku.com', 'suumo.jp', 'athome.co.jp', 'homes.co.jp', 'ikyu.com', 'travel.rakuten.co.jp', 'jtb.co.jp', 'yame.mypl.net', 'mypl.net', 'ekiten.jp']

def classify_url(url):
    if not url:
        return "", "", ""
    url_lower = url.lower()
    for domain in SNS_DOMAINS:
        if domain in url_lower:
            return "", url, ""
    for domain in PORTAL_DOMAINS:
        if domain in url_lower:
            return "", "", url
    return url, "", ""

def get_auth_header():
    credentials = f"{API_LOGIN}:{API_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}

def parse_phone(phone_raw):
    if not phone_raw:
        return ""
    phone_raw = phone_raw.strip()
    if phone_raw.startswith("+81"):
        return "0" + phone_raw[3:].lstrip("-")
    return phone_raw

def fetch_single(keyword, area):
    url = "https://api.dataforseo.com/v3/serp/google/maps/live/advanced"
    payload = [{"keyword": f"{keyword} {area}", "location_name": "Japan", "language_name": "Japanese", "depth": 700}]
    try:
        response = requests.post(url, headers=get_auth_header(), json=payload, timeout=60)
        data = response.json()
        if data.get("status_code") != 20000:
            return [], False
        results = []
        for task in data.get("tasks", []):
            if task.get("status_code") != 20000:
                continue
            for result in task.get("result", []):
                for item in result.get("items", []):
                    if item.get("type") != "maps_search":
                        continue
                    address_info = item.get("address_info", {}) or {}
                    zip_code = address_info.get("zip", "") or ""
                    region = address_info.get("region", "") or ""
                    city = address_info.get("city", "") or ""
                    address_detail = address_info.get("address", "") or ""
                    full_address = f"{region}{city}{address_detail}"
                    phone = parse_phone(item.get("phone", ""))
                    raw_url = item.get("url", "") or ""
                    website_url, sns_url, other_url = classify_url(raw_url)
                    place_id = item.get("place_id", "") or ""
                    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""
                    rating = item.get("rating", {}) or {}
                    rating_value = rating.get("value", "") if isinstance(rating, dict) else ""
                    rating_count = rating.get("votes_count", "") if isinstance(rating, dict) else ""
                    category = item.get("category", "")
                    add_cats = item.get("additional_categories", []) or []
                    all_cats = [category] + add_cats if category else add_cats
                    category_str = ", ".join([c for c in all_cats if c])
                    results.append({
                        "業種": keyword, "エリア": area,
                        "店舗名": item.get("title", ""),
                        "郵便番号": zip_code, "住所": full_address,
                        "電話番号": phone, "WebサイトURL": website_url,
                        "SNS URL": sns_url, "その他URL": other_url,
                        "評価": rating_value, "口コミ数": rating_count,
                        "カテゴリ": category_str, "GoogleマップURL": maps_url,
                    })
        hit_limit = len(results) >= 700
        return results, hit_limit
    except Exception as e:
        return [], False

def fetch_google_maps(keyword, area, progress_cb=None):
    results, hit_limit = fetch_single(keyword, area)
    if hit_limit and area in CITY_DISTRICTS:
        districts = CITY_DISTRICTS[area]
        results = []
        for i, district in enumerate(districts):
            if progress_cb:
                progress_cb(f"📍 {district} を検索中... ({i+1}/{len(districts)})")
            sub_results, _ = fetch_single(keyword, district)
            results.extend(sub_results)
            time.sleep(0.5)
    return results, hit_limit

def deduplicate(results):
    seen = set()
    unique = []
    for r in results:
        maps_url = r.get("GoogleマップURL", "")
        key = maps_url if maps_url and "place_id:" in maps_url else (r["店舗名"] + r["住所"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

def to_csv(results):
    output = io.StringIO()
    fieldnames = ["業種", "エリア", "店舗名", "郵便番号", "住所", "電話番号", "WebサイトURL", "SNS URL", "その他URL", "評価", "口コミ数", "カテゴリ", "GoogleマップURL"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue().encode("utf-8-sig")

# ========== UI ==========
st.markdown("""
<div class="hyn-header">
    <h1>🗾 営業リスト抽出ツール</h1>
    <p>© HYN株式会社 ／ Powered by DataForSEO</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="card"><h3>📍 エリア選択</h3>', unsafe_allow_html=True)
    pref = st.selectbox("都道府県", list(AREAS.keys()), index=list(AREAS.keys()).index("福岡県"))
    cities = [c for c in AREAS[pref] if c != "その他（直接入力）"]
    city_options = cities + ["その他（直接入力）"]
    selected_cities = st.multiselect("市区町村（複数選択可）", city_options, default=[cities[0]] if cities else [])
    custom_area = ""
    if "その他（直接入力）" in selected_cities:
        custom_area = st.text_input("エリアを直接入力")
    final_areas = [c for c in selected_cities if c != "その他（直接入力）"]
    if custom_area:
        final_areas.append(custom_area)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><h3>🏢 業種選択</h3>', unsafe_allow_html=True)
    big_cat = st.selectbox("大カテゴリ", list(CATEGORIES.keys()))
    sub_cats = list(CATEGORIES[big_cat].keys())
    selected_subs = st.multiselect("中カテゴリ（複数選択可）", sub_cats, default=[sub_cats[0]] if sub_cats else [])
    custom_gyoshu = st.text_input("業種を直接入力（任意）")
    final_gyoshu = selected_subs.copy()
    if custom_gyoshu:
        final_gyoshu.append(custom_gyoshu)
    st.markdown('</div>', unsafe_allow_html=True)

# 設定確認
if final_areas and final_gyoshu:
    total_queries = len(final_areas) * len(final_gyoshu)
    st.markdown(f"""
    <div class="result-box">
        📋 <b>設定確認</b>：
        エリア {len(final_areas)}件 × 業種 {len(final_gyoshu)}件 ＝ <b>{total_queries}クエリ</b>
        <br>エリア: {', '.join(final_areas)}　業種: {', '.join(final_gyoshu)}
    </div>
    """, unsafe_allow_html=True)

# ========== セッションステート初期化 ==========
if 'extraction_done' not in st.session_state:
    st.session_state.extraction_done = False
    st.session_state.results_data = None
    st.session_state.areas_extracted = ""
    st.session_state.results_count = 0
    st.session_state.dedup_count = 0

# 抽出ボタン
if st.button("🔍 抽出開始", disabled=not (final_areas and final_gyoshu)):
    all_results = []
    total_queries = len(final_areas) * len(final_gyoshu)
    progress_bar = st.progress(0)
    status = st.empty()
    log = st.empty()
    count = 0

    for area in final_areas:
        for gyoshu in final_gyoshu:
            count += 1
            status.markdown(f"⏳ **[{count}/{total_queries}]** 「{gyoshu} {area}」を検索中...")
            def cb(msg):
                log.markdown(f"<div class='split-box'>⚡ {msg}</div>", unsafe_allow_html=True)
            results, hit_limit = fetch_google_maps(gyoshu, area, progress_cb=cb)
            if hit_limit and area in CITY_DISTRICTS:
                log.markdown(f"<div class='warn-box'>⚠️ 700件上限 → {area}を区単位に自動分割して再取得しました</div>", unsafe_allow_html=True)
            all_results.extend(results)
            progress_bar.progress(count / total_queries)
            if count < total_queries:
                time.sleep(0.5)

    unique_results = deduplicate(all_results)
    dedup_count = len(all_results) - len(unique_results)
    log.empty()
    status.empty()
    progress_bar.progress(1.0)

    # ========== セッションステートに保存 ==========
    st.session_state.extraction_done = True
    st.session_state.results_data = unique_results
    st.session_state.areas_extracted = ", ".join(final_areas)
    st.session_state.results_count = len(all_results)
    st.session_state.dedup_count = dedup_count

# ========== 抽出結果表示（セッションステート使用） ==========
if st.session_state.extraction_done and st.session_state.results_data:
    unique_results = st.session_state.results_data
    
    st.markdown(f"""
    <div class="result-box">
        ✅ <b>抽出完了！</b><br>
        取得件数: {st.session_state.results_count}件 → 重複除去: {st.session_state.dedup_count}件 → <b>{len(unique_results)}件</b>
    </div>
    """, unsafe_allow_html=True)

    if unique_results:
        csv_data = to_csv(unique_results)
        from datetime import datetime
        
        # ファイル名を改善（複数地区対応）
        areas_short = st.session_state.areas_extracted[:20] if len(st.session_state.areas_extracted) > 20 else st.session_state.areas_extracted
        filename = f"営業リスト_{areas_short}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            key="download_csv"  # ユニークキーを明示的に設定
        )

        # プレビュー
        import pandas as pd
        df = pd.DataFrame(unique_results)
        st.markdown("#### プレビュー（最初の10件）")
        st.dataframe(df.head(10), use_container_width=True)
