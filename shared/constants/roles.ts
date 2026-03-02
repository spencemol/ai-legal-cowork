export enum UserRole {
  Attorney = 'attorney',
  Paralegal = 'paralegal',
  Partner = 'partner',
}

export enum AccessLevel {
  Full = 'full',
  Restricted = 'restricted',
  ReadOnly = 'read_only',
}

export enum MatterStatus {
  Active = 'active',
  Closed = 'closed',
  Archived = 'archived',
}

export enum DocumentStatus {
  Pending = 'pending',
  Processing = 'processing',
  Indexed = 'indexed',
  Failed = 'failed',
}

export enum MessageRole {
  User = 'user',
  Assistant = 'assistant',
}

export enum ClientRole {
  Plaintiff = 'plaintiff',
  Defendant = 'defendant',
  ThirdParty = 'third_party',
  Other = 'other',
}
