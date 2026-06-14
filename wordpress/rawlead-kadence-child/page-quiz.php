<?php
/**
 * Template: /quiz — match-first onboarding.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<main id="primary" class="rl-app rl-app--quiz site-main" data-rl-app="quiz">
	<div class="rl-container rl-quiz-wrap">
		<?php rawlead_get_part('quiz'); ?>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
