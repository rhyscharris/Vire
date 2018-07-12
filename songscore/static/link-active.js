$(window, document, undefined).ready(function() {
  $(function(){
      var current = location.pathname;
      $('.selector ul li a').each(function(){
          var $this = $(this);
          // if the current path is like 'this' link, add the active class
          if($this.attr('href').indexOf(current) !== -1){
              $this.addClass('link-active');
          }
      })
      $('.navigation ul li a').each(function(){
          var $this = $(this);
          // if the current path is like 'this' link, add the active class
          if($this.attr('href').indexOf(current) !== -1){
              $this.addClass('link-active');
          }
      })
  })
});
