
DEST_DIR=/home/damon/gem5_loop/gem5/SPEC_Results/507_simpoint/restore_novp_3

CONFIG=config.json
STATS=stats.txt
TEMPLATE=template.xml
TEMPLATE_SPEC=template_spec.xml


all: template mcpat

spec: template_spec mcpat

template_spec:
	python2.7 /home/damon/gem5_loop/gem5/Gem5ToMcPAT-Parser/Gem5ToMcPAT-Parser-spec.py -c ${DEST_DIR}/${CONFIG} -s ${DEST_DIR}/${STATS} -t /home/damon/gem5_loop/gem5/Gem5ToMcPAT-Parser/${TEMPLATE_SPEC} -o ${DEST_DIR}/mcpat.xml

template:
	python2.7 /home/damon/gem5_loop/gem5/Gem5ToMcPAT-Parser/Gem5ToMcPAT-Parser.py -c ${DEST_DIR}/${CONFIG} -s ${DEST_DIR}/${STATS} -t /home/damon/gem5_loop/gem5/Gem5ToMcPAT-Parser/${TEMPLATE} -o ${DEST_DIR}/mcpat.xml

mcpat:
	/home/damon/gem5_loop/gem5/mcpat/mcpat -infile ${DEST_DIR}/mcpat.xml -print_level 5 > ${DEST_DIR}/mcpat.log
