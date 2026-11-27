import { PosterHeading } from "@/components/poster-heading";
import { PostRow } from "@/components/post-row";
import { Container } from "@/components/ui/container";
import { TextLink } from "@/components/ui/text-link";
import { getPosts, readAtRequestTimeWithoutApi } from "@/lib/api/public";

const LATEST = 3;

/** The newest posts as hover-flood rows (PostRow). Left out when nothing is published. */
export async function WritingRows() {
  await readAtRequestTimeWithoutApi();
  const { items } = await getPosts({ size: LATEST });
  if (items.length === 0) {
    return null;
  }
  return (
    // overflow-x-clip: the flood runs to the screen's edges, never past them.
    <section className="below-fold overflow-x-clip border-t border-line py-20 sm:py-28">
      <Container className="flex flex-col gap-12">
        <PosterHeading title="Latest writing" action={<TextLink href="/blog">See all posts</TextLink>} />
        <ul className="border-t border-line">
          {items.map((post, index) => (
            <PostRow key={post.id} post={post} index={index} />
          ))}
        </ul>
      </Container>
    </section>
  );
}
