
function reload_stats(data, blocks) {
    for(i = 0; i < blocks.length; i++) {
        var block = data[blocks[i]];

        if(block) {
            var name = `#${blocks[i]}`;
            $(name).html(block);
        }
    }
}
