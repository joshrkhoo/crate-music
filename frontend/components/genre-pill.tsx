type GenrePillProps = {
  genre: string;
};

export function GenrePill({ genre }: GenrePillProps) {
  return <span className="crate-genre">{genre}</span>;
}
