import { humanize } from "../api/constants";

interface Props {
  value: string;
}

/** Small coloured pill for category / priority / status values. */
export function Badge({ value }: Props) {
  return <span className={`badge badge-${value}`}>{humanize(value)}</span>;
}