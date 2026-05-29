<?php
/**
 * Inner marketing pages (how, pricing, faq, contact).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

if (!rawlead_is_inner_shell_page()) {
    $parent_page = get_template_directory() . '/page.php';
    if (is_readable($parent_page)) {
        include $parent_page;
        return;
    }
}

get_header();
rawlead_get_part('header');

$post = get_queried_object();
$slug = $post instanceof WP_Post ? $post->post_name : '';
$lead = rawlead_inner_page_lead($slug);
?>
<main id="primary" class="rl-inner site-main">
	<?php
	while (have_posts()) {
		the_post();
		?>
		<article id="post-<?php the_ID(); ?>" <?php post_class('rl-inner-article'); ?>>
			<header class="rl-inner-hero">
				<div class="rl-container">
					<p class="rl-inner-hero__eyebrow">RawLead</p>
					<h1 class="rl-inner-hero__title"><?php the_title(); ?></h1>
					<?php if ($lead !== '') : ?>
						<p class="rl-inner-hero__lead"><?php echo esc_html($lead); ?></p>
					<?php endif; ?>
				</div>
			</header>
			<div class="rl-container rl-inner-body">
				<div class="entry-content rl-prose">
					<?php
					$inner_html = rawlead_inner_page_html($slug);
					if ($inner_html !== null) {
						echo wp_kses_post($inner_html);
					} else {
						the_content();
					}
					?>
				</div>
			</div>
		</article>
		<?php
	}
	?>
</main>
<?php
rawlead_get_part('footer');
get_footer();
