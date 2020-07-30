
function reload_stats(data, blocks) {
    for(i = 0; i < blocks.length; i++) {
        var name = `#${blocks[i]}`;
        var block = $(data).filter(name).html();
        if(block) {
            $(name).html(block);
        }
    }
}
