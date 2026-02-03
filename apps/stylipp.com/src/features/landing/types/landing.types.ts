export interface NavItem {
  label: string
  href?: string
  children?: NavItem[]
}

export interface Testimonial {
  id: string
  companyLogo: string
  companyName: string
  quote: string
  fullText: string
  authorName: string
  authorRole: string
}

export interface Feature {
  id: string
  icon: React.ReactNode
  title: string
  description: string
}

export interface Benefit {
  id: string
  icon: React.ReactNode
  title: string
  description: string
}

export interface PartnerLogo {
  id: string
  name: string
  src: string
}
