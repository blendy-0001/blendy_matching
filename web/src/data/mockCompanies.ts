import { Company, CompanyAttributes, CompanyProfile } from "@/lib/types";

export interface MockCompany {
  company: Company;
  profile: CompanyProfile;
  attributes: CompanyAttributes;
}

/** DB 未接続でもUIが動くようにするモック企業群。 */
export const MOCK_COMPANIES: MockCompany[] = [
  {
    company: {
      id: "c1",
      name: "アトラスSaaS",
      industry: "IT",
      employeeCount: 35,
      revenueScale: "1〜5億",
      websiteUrl: "https://example.com/atlas",
    },
    profile: {
      companyId: "c1",
      summary:
        "中小企業向けの業務自動化SaaSを開発・提供。導入から定着支援までを一気通貫で行う。",
      valueProp: "バックオフィス業務の自動化で、現場の工数を平均30%削減。",
      strengths: "プロダクト開発力、クラウドネイティブな実装、定着支援。",
      challenges: "新規顧客の獲得チャネルが限られ、営業リソースが不足。",
      targetMarket: "従業員50〜300名のサービス業・製造業。",
      isEdited: true,
    },
    attributes: {
      activities: ["勉強会・セミナー登壇", "SNS・オンライン発信"],
      decisionStyle: "慎重派",
      timeHorizon: "長期",
      commitmentLevel: 5,
      collaborationStyle: "協調志向",
      pastCollaboration: "1-2回",
    },
  },
  {
    company: {
      id: "c2",
      name: "リンクセールス",
      industry: "サービス",
      employeeCount: 60,
      revenueScale: "5〜10億",
      websiteUrl: "https://example.com/link",
    },
    profile: {
      companyId: "c2",
      summary: "BtoB営業代行・インサイドセールス支援。商談獲得に強み。",
      valueProp: "見込み客の発掘から商談化までを代行し、受注機会を最大化。",
      strengths: "営業組織の構築、アウトバウンド、顧客基盤。",
      challenges: "提供できるプロダクトを持たず、案件の幅を広げたい。",
      targetMarket: "プロダクトを持つスタートアップ・SaaS企業。",
      isEdited: true,
    },
    attributes: {
      activities: ["交流会・ミートアップ参加", "紹介・リファラル活動"],
      decisionStyle: "即決派",
      timeHorizon: "長期",
      commitmentLevel: 4,
      collaborationStyle: "協調志向",
      pastCollaboration: "3回以上",
    },
  },
  {
    company: {
      id: "c3",
      name: "ミナトデザイン",
      industry: "メディア",
      employeeCount: 12,
      revenueScale: "1億未満",
      websiteUrl: "https://example.com/minato",
    },
    profile: {
      companyId: "c3",
      summary: "ブランディング・UIデザインに特化したクリエイティブスタジオ。",
      valueProp: "事業の世界観を可視化し、プロダクトとマーケの一貫性をつくる。",
      strengths: "デザイン、ブランド設計、クリエイティブ制作。",
      challenges: "開発・実装パートナーが不足し、上流で止まることがある。",
      targetMarket: "リブランディングを検討する成長期の企業。",
      isEdited: true,
    },
    attributes: {
      activities: ["SNS・オンライン発信", "勉強会・セミナー登壇"],
      decisionStyle: "バランス型",
      timeHorizon: "中期",
      commitmentLevel: 3,
      collaborationStyle: "バランス",
      pastCollaboration: "1-2回",
    },
  },
  {
    company: {
      id: "c4",
      name: "ヘルスブリッジ",
      industry: "医療",
      employeeCount: 120,
      revenueScale: "10億以上",
      websiteUrl: "https://example.com/health",
    },
    profile: {
      companyId: "c4",
      summary: "医療機関向けの予約・問診DXを展開。地域医療連携に強み。",
      valueProp: "患者体験と医療現場の業務を同時に改善するプラットフォーム。",
      strengths: "医療業界の顧客基盤、業界知見、現場導入の実績。",
      challenges: "AI・データ活用の内製が追いつかず、技術連携先を探している。",
      targetMarket: "クリニック・中規模病院・自治体。",
      isEdited: true,
    },
    attributes: {
      activities: ["副事業・副次サービスへの投資", "交流会・ミートアップ参加"],
      decisionStyle: "慎重派",
      timeHorizon: "長期",
      commitmentLevel: 4,
      collaborationStyle: "協調志向",
      pastCollaboration: "3回以上",
    },
  },
];

/** ログイン中の「自社」を模したモック（ランキングの基準）。 */
export const MOCK_SELF_ATTRIBUTES: CompanyAttributes = {
  activities: ["交流会・ミートアップ参加", "SNS・オンライン発信"],
  decisionStyle: "即決派",
  timeHorizon: "長期",
  commitmentLevel: 5,
  collaborationStyle: "協調志向",
  pastCollaboration: "1-2回",
};
