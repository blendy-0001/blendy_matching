import requests
import json

url = 'http://localhost:8000/register-multiactivity'

# Prepare form data
data = {
    '名前': 'テスト太郎2',
    '会社名': 'テスト企業2',
    '業種カテゴリ': 'テック',
    '業種詳細': 'SaaS開発',
    '事業フェーズ': '成長期',
    'LINE_ID': '@test_taro_2023',
    'Facebook_URL': 'https://facebook.com/test.taro.2',
    '活動1_名称': 'Web開発支援',
    '活動1_サービス': 'フルスタック開発コンサル',
    '活動1_対象業界': '金融',
    '活動1_対象企業規模': '大企業',
    '活動1_強み詳細': 'Vue.js と Python での開発経験',
    '活動1_課題詳細': 'クラウド化対応',
    '活動1_強み': ['Web開発', 'API設計'],
    '活動1_課題': ['クラウド移行'],
    '活動1_ポジション': ['エンジニア'],
    '活動2_名称': '営業戦略コンサル',
    '活動2_サービス': '営業組織構築支援',
    '活動2_対象業界': 'SaaS',
    '活動2_対象企業規模': 'スタートアップ',
    '活動2_強み詳細': 'スタートアップ営業スケール経験',
    '活動2_課題詳細': '営業人材採用',
    '活動2_強み': ['営業戦略', '営業支援'],
    '活動2_課題': ['人材育成'],
    '活動2_ポジション': ['営業'],
    '活動3_名称': '人事戦略',
    '活動3_サービス': '組織開発コンサル',
    '活動3_対象業界': 'テック',
    '活動3_対象企業規模': 'スタートアップ',
    '活動3_強み詳細': 'ベンチャー企業の採用・組織化経験',
    '活動3_課題詳細': '人事制度設計',
    '活動3_強み': ['人事戦略'],
    '活動3_課題': ['組織変革'],
    '活動3_ポジション': ['企画'],
}

try:
    response = requests.post(url, data=data, timeout=10)
    result = response.json()
    
    print('✅ テストメンバー登録成功！\n')
    print('📊 登録情報:')
    print(f"   名前: {data['名前']}")
    print(f"   LINE ID: {data['LINE_ID']}")
    print(f"   Facebook URL: {data['Facebook_URL']}")
    print(f"   アクティビティ: 3 件")
    if 'page_id' in result:
        print(f"   Member Page ID: {result['page_id']}")
except Exception as e:
    print(f'❌ エラー: {str(e)}')
