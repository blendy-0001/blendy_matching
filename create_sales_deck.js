const PptxGenJS = require('pptxgenjs');

// プレゼンテーション初期化
const pres = new PptxGenJS();
pres.defineLayout({ name: 'LAYOUT1', width: 10, height: 5.625 });
pres.defineLayout({ name: 'LAYOUT2', width: 10, height: 5.625 });
pres.defineLayout({ name: 'LAYOUT3', width: 10, height: 5.625 });

// カラーパレット定義（Blendy Inc. イメージ）
const colors = {
  dark: '1E2761',      // ネイビー（信頼）
  light: 'CADCFC',     // アイスブルー（爽やか）
  accent: 'FF6B6B',    // コーラル（エネルギー）
  white: 'FFFFFF',
  text: '333333'
};

// フォント設定
const fontTitle = { name: 'Arial', size: 44, bold: true, color: colors.white };
const fontSubtitle = { name: 'Arial', size: 28, bold: true, color: colors.dark };
const fontBody = { name: 'Arial', size: 14, color: colors.text };
const fontSmall = { name: 'Arial', size: 12, color: '#666666' };

// ============================================
// スライド 1: タイトルスライド
// ============================================
let slide1 = pres.addSlide();
slide1.background = { color: colors.dark };

slide1.addText('協業マッチングシステム', {
  x: 0.5, y: 1.8, w: 9, h: 0.8,
  fontSize: 48, bold: true, color: colors.white,
  align: 'center'
});

slide1.addText('最適なパートナーシップで、事業を拡大させる', {
  x: 0.5, y: 2.7, w: 9, h: 0.6,
  fontSize: 20, color: colors.light,
  align: 'center'
});

slide1.addText('Blendy Inc.', {
  x: 0.5, y: 4.5, w: 9, h: 0.4,
  fontSize: 16, color: colors.light,
  align: 'center'
});

// ============================================
// スライド 2: 問題提起
// ============================================
let slide2 = pres.addSlide();
slide2.background = { color: colors.white };

// タイトル
slide2.addText('現状の課題', {
  x: 0.5, y: 0.3, w: 9, h: 0.5,
  fontSize: 36, bold: true, color: colors.dark
});

// 課題をアイコンスタイルで表示
const issues = [
  { title: '営業効率が低い', desc: '営業対象を見つけるのに時間がかかる' },
  { title: 'リード獲得が困難', desc: '新規顧客へのアプローチ方法が限定的' },
  { title: '相性の悪いマッチング', desc: '適切でないパートナーとの提携により失敗のリスク' }
];

issues.forEach((issue, idx) => {
  const yPos = 1.2 + (idx * 1.2);

  // 背景ボックス
  slide2.addShape(pres.ShapeType.rect, {
    x: 0.5, y: yPos, w: 9, h: 1,
    fill: { color: '#F5F5F5' },
    line: { color: colors.accent, width: 3 }
  });

  // タイトル
  slide2.addText(issue.title, {
    x: 0.8, y: yPos + 0.1, w: 8.4, h: 0.35,
    fontSize: 16, bold: true, color: colors.accent
  });

  // 説明
  slide2.addText(issue.desc, {
    x: 0.8, y: yPos + 0.45, w: 8.4, h: 0.4,
    fontSize: 12, color: colors.text
  });
});

// ============================================
// スライド 3: ソリューション
// ============================================
let slide3 = pres.addSlide();
slide3.background = { color: colors.white };

// タイトル
slide3.addText('Blendy の解決策', {
  x: 0.5, y: 0.3, w: 9, h: 0.5,
  fontSize: 36, bold: true, color: colors.dark
});

// ソリューションポイント
const solutions = [
  {
    icon: '🤖',
    title: 'AI マッチング',
    desc: '複数の評価軸で最適なパートナーを自動選定'
  },
  {
    icon: '⚡',
    title: '時間削減',
    desc: '営業活動の準備時間を 80% 削減'
  },
  {
    icon: '✓',
    title: '成功率向上',
    desc: '相性スコアに基づいた信頼できるマッチング'
  }
];

solutions.forEach((sol, idx) => {
  const xPos = 0.5 + (idx * 3.2);

  // アイコン背景
  slide3.addShape(pres.ShapeType.ellipse, {
    x: xPos + 0.6, y: 1.2, w: 1, h: 1,
    fill: { color: colors.light },
    line: { color: colors.dark, width: 2 }
  });

  // アイコン
  slide3.addText(sol.icon, {
    x: xPos + 0.6, y: 1.25, w: 1, h: 1,
    fontSize: 32, align: 'center', valign: 'middle'
  });

  // タイトル
  slide3.addText(sol.title, {
    x: xPos, y: 2.4, w: 3, h: 0.4,
    fontSize: 14, bold: true, color: colors.dark, align: 'center'
  });

  // 説明
  slide3.addText(sol.desc, {
    x: xPos, y: 2.9, w: 3, h: 0.8,
    fontSize: 11, color: colors.text, align: 'center', valign: 'top'
  });
});

// ============================================
// スライド 4: ビジネスモデル
// ============================================
let slide4 = pres.addSlide();
slide4.background = { color: colors.white };

// タイトル
slide4.addText('ビジネスモデル', {
  x: 0.5, y: 0.3, w: 9, h: 0.5,
  fontSize: 36, bold: true, color: colors.dark
});

// 料金体系
const pricingTitle = slide4.addText('成果報酬型（紹介される側のみ支払い）', {
  x: 0.5, y: 1.0, w: 9, h: 0.4,
  fontSize: 14, bold: true, color: colors.accent
});

const pricingItems = [
  { label: '性格マッチング', price: '¥5,000', desc: 'スキルセット相互補完なし' },
  { label: '業種 + 性格マッチング', price: '¥10,000', desc: 'スキルセット相互補完あり' },
  { label: '1商談（成約可能性高）', price: '¥25,000', desc: '3組セット' }
];

let yPos = 1.6;
pricingItems.forEach((item) => {
  slide4.addShape(pres.ShapeType.rect, {
    x: 0.5, y: yPos, w: 9, h: 0.65,
    fill: { color: '#F0F4FF' },
    line: { color: colors.light, width: 1 }
  });

  slide4.addText(item.label, {
    x: 0.8, y: yPos + 0.08, w: 4, h: 0.25,
    fontSize: 13, bold: true, color: colors.dark
  });

  slide4.addText(item.price, {
    x: 5.5, y: yPos + 0.08, w: 3, h: 0.25,
    fontSize: 14, bold: true, color: colors.accent, align: 'right'
  });

  slide4.addText(item.desc, {
    x: 0.8, y: yPos + 0.38, w: 8.2, h: 0.22,
    fontSize: 10, color: '#666666'
  });

  yPos += 0.75;
});

// ============================================
// スライド 5: 導入実績
// ============================================
let slide5 = pres.addSlide();
slide5.background = { color: colors.white };

// タイトル
slide5.addText('導入実績', {
  x: 0.5, y: 0.3, w: 9, h: 0.5,
  fontSize: 36, bold: true, color: colors.dark
});

// 統計情報
const stats = [
  { number: '13', label: '登録メンバー', color: colors.dark },
  { number: '60', label: 'マッチング可能組数', color: colors.accent },
  { number: '18', label: '累計マッチング完了', color: colors.light }
];

stats.forEach((stat, idx) => {
  const xPos = 1.5 + (idx * 3);

  slide5.addShape(pres.ShapeType.rect, {
    x: xPos, y: 1.3, w: 2.5, h: 2.5,
    fill: { color: stat.color },
    line: { type: 'none' }
  });

  slide5.addText(stat.number, {
    x: xPos, y: 2.0, w: 2.5, h: 0.7,
    fontSize: 52, bold: true, color: colors.white, align: 'center', valign: 'middle'
  });

  slide5.addText(stat.label, {
    x: xPos, y: 2.8, w: 2.5, h: 0.6,
    fontSize: 14, color: colors.white, align: 'center', valign: 'top'
  });
});

// ============================================
// スライド 6: 利用方法
// ============================================
let slide6 = pres.addSlide();
slide6.background = { color: colors.white };

// タイトル
slide6.addText('簡単 3ステップ', {
  x: 0.5, y: 0.3, w: 9, h: 0.5,
  fontSize: 36, bold: true, color: colors.dark
});

// ステップ
const steps = [
  { num: '1', title: '登録', desc: 'フォームに企業情報を入力' },
  { num: '2', title: 'マッチング実行', desc: 'AI が最適なパートナーを自動選定' },
  { num: '3', title: '紹介・成約', desc: 'Blendy が契約までサポート' }
];

steps.forEach((step, idx) => {
  const xPos = 0.8 + (idx * 3);

  // ステップ番号
  slide6.addShape(pres.ShapeType.ellipse, {
    x: xPos + 0.9, y: 1.3, w: 0.6, h: 0.6,
    fill: { color: colors.accent },
    line: { type: 'none' }
  });

  slide6.addText(step.num, {
    x: xPos + 0.9, y: 1.3, w: 0.6, h: 0.6,
    fontSize: 28, bold: true, color: colors.white, align: 'center', valign: 'middle'
  });

  // タイトル
  slide6.addText(step.title, {
    x: xPos, y: 2.1, w: 2.6, h: 0.35,
    fontSize: 16, bold: true, color: colors.dark, align: 'center'
  });

  // 説明
  slide6.addText(step.desc, {
    x: xPos, y: 2.5, w: 2.6, h: 1,
    fontSize: 11, color: colors.text, align: 'center', valign: 'top'
  });

  // 矢印（最後のステップを除く）
  if (idx < 2) {
    slide6.addText('→', {
      x: xPos + 2.7, y: 1.5, w: 0.3, h: 0.3,
      fontSize: 20, color: colors.accent, align: 'center'
    });
  }
});

// ============================================
// スライド 7: まとめ
// ============================================
let slide7 = pres.addSlide();
slide7.background = { color: colors.dark };

slide7.addText('Blendy で実現する', {
  x: 0.5, y: 1.5, w: 9, h: 0.6,
  fontSize: 40, bold: true, color: colors.light, align: 'center'
});

slide7.addText('最適なパートナーシップ', {
  x: 0.5, y: 2.2, w: 9, h: 0.6,
  fontSize: 40, bold: true, color: colors.white, align: 'center'
});

slide7.addText('お気軽にお問い合わせください', {
  x: 0.5, y: 3.5, w: 9, h: 0.4,
  fontSize: 16, color: colors.light, align: 'center'
});

slide7.addText('contact@blendyinc.com', {
  x: 0.5, y: 4.0, w: 9, h: 0.4,
  fontSize: 14, color: colors.white, align: 'center'
});

// ============================================
// 保存
// ============================================
pres.save({ path: 'C:\\Users\\yo_yo\\Documents\\blendy_matching\\営業資料_たたき.pptx' });

console.log('✅ 営業資料を作成しました: 営業資料_たたき.pptx');
