<?php
/**
 * Front page — editorial landing (REFERENCE §3).
 * Plugin rawlead-landing keeps page content in DB; this template renders the marketing layout.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<main id="primary" class="rl-landing rl-scroll-experience site-main">
	<?php
	rawlead_get_part('hero');
	rawlead_get_part('flow');
	rawlead_get_part('manifest');
	rawlead_get_part('features');
	rawlead_get_part('audience');
	rawlead_get_part('pricing-preview');
	?>
</main>
<?php
rawlead_get_part('footer');
get_footer();
